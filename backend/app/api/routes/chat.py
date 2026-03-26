"""
Chat API Routes
Q&A with documents using LangGraph
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from bson import ObjectId
from datetime import datetime, timezone
import uuid

from ...models.chat import ChatRequest, ChatResponse, ChatMessage
from ...models.user import UserResponse
from ...config import settings
from ...services.rag.workflow import create_rag_workflow
from ...services.shared.lexical_service import LexicalBM25Service
from ...api.deps import (
    get_milvus_service,
    get_embedding_service,
    get_llm_service,
    get_mcq_service,
    get_summarizer_service,
    get_faq_service,
    get_input_guardrails_service,
    get_query_router_service,
    get_simple_response_handler
)
from ...database.mongodb_client import get_mongodb, MongoDBClient
from ..routes.auth import get_current_user
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb),
    milvus=Depends(get_milvus_service),
    embedding_service=Depends(get_embedding_service),
    llm_service=Depends(get_llm_service),
    mcq_service=Depends(get_mcq_service),
    summarizer_service=Depends(get_summarizer_service),
    faq_service=Depends(get_faq_service)
):
    """
    Chat with documents using RAG
    
    Uses LangGraph workflow:
    1. Retrieve relevant chunks
    2. Grade relevance
    3. Rewrite query if needed
    4. Generate answer
    """
    # Verify notebook belongs to user
    try:
        notebook_doc = mongodb.notebooks.find_one({
            "_id": ObjectId(request.notebook_id),
            "user_id": current_user.id
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    if not notebook_doc:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    try:
        # Check for special commands
        if request.message.startswith("/"):
            return await handle_command(
                request=request,
                notebook_doc=notebook_doc,
                current_user=current_user,
                mongodb=mongodb,
                milvus=milvus,
                embedding_service=embedding_service,
                llm_service=llm_service,
                mcq_service=mcq_service,
                summarizer_service=summarizer_service,
                faq_service=faq_service
            )

        # === NEW: Input Guardrails + Intelligent Routing ===
        # (Feature-flagged via settings; default enabled)
        if getattr(settings, "ENABLE_INPUT_GUARDRAILS", True):
            guardrails = get_input_guardrails_service()
            validation = await guardrails.validate_input(request.message)
            if not validation.get("passed", True):
                logger.warning(f"Input rejected: {validation.get('reason')}")
                return ChatResponse(
                    message=f"⚠️ {validation.get('reason')}",
                    sources=[],
                    citations=[],
                    web_sources=[],
                    metadata={
                        "guardrail_rejected": True,
                        "severity": validation.get("severity", "info")
                    },
                    chat_history=request.chat_history or []
                )

        if getattr(settings, "ENABLE_INTELLIGENT_ROUTING", True):
            router = get_query_router_service()
            routing = await router.route_query(
                query=request.message,
                chat_history=request.chat_history or []
            )
            logger.info(f"Query routed to: {routing.get('route')} (method={routing.get('method')}, conf={routing.get('confidence')})")

            if routing.get("route") and routing.get("route") != "retrieval_needed":
                handler = get_simple_response_handler()
                route = routing.get("route")
                if route == "greeting":
                    answer = await handler.handle_greeting(request.message)
                elif route == "chitchat":
                    answer = await handler.handle_chitchat(request.message, request.chat_history or [])
                elif route == "meta":
                    answer = await handler.handle_meta(request.message, notebook_doc.get("name"))
                elif route == "out_of_scope":
                    answer = await handler.handle_out_of_scope(request.message)
                else:
                    answer = await handler.handle_chitchat(request.message, request.chat_history or [])

                updated_history = (request.chat_history or []).copy()
                updated_history.append(ChatMessage(role="user", content=request.message))
                updated_history.append(ChatMessage(role="assistant", content=answer))

                return ChatResponse(
                    message=answer,
                    sources=[],
                    citations=[],
                    web_sources=[],
                    metadata={
                        "route": route,
                        "routing_method": routing.get("method"),
                        "routing_confidence": routing.get("confidence"),
                    },
                    chat_history=updated_history
                )
        
        # Create and run RAG workflow (lexical-first)
        lexical_service = LexicalBM25Service(milvus)
        workflow = create_rag_workflow(
            milvus_service=milvus,
            embedding_service=embedding_service,
            llm_service=llm_service,
            lexical_service=lexical_service
        )
        
        # Log web search status
        logger.info(f"Chat request - enable_web_search: {request.enable_web_search}")
        
        # Run the graph with enable_web_search flag
        result = await workflow.ainvoke({
            "question": request.message,
            "notebook_id": request.notebook_id,
            "chat_history": request.chat_history or [],
            "force_web_search": request.enable_web_search  # NEW: Force web search if enabled
        })

        # Build updated chat history
        updated_history = (request.chat_history or []).copy()
        updated_history.append(ChatMessage(role="user", content=request.message))
        updated_history.append(ChatMessage(role="assistant", content=result["answer"]))

        # Log citations for debugging
        citations = result.get("citations", [])
        logger.info(f"API returning {len(citations)} citations to frontend")
        if citations:
            logger.info(f"First citation: file_type={citations[0].get('file_type')}, filename={citations[0].get('filename')}")

        return ChatResponse(
            message=result["answer"],
            sources=result.get("sources", []),
            citations=citations,  # Enhanced citations
            web_sources=result.get("web_sources", []),
            metadata={
                "workflow_steps": result.get("steps", []),
                "retrieval_count": result.get("retrieval_count", 0),
                "used_web_search": result.get("used_web_search", False)
            },
            chat_history=updated_history
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_command(
    request,
    notebook_doc,
    current_user,
    mongodb,
    milvus,
    embedding_service,
    llm_service,
    mcq_service,
    summarizer_service,
    faq_service
):
    """Handle special commands like /quiz, /summary, etc."""
    message = request.message.lower()
    notebook_id = request.notebook_id
    
    if message.startswith("/quiz"):
        # Parse number of questions
        parts = message.split()
        num_questions = 5  # default
        if len(parts) > 1:
            try:
                num_questions = int(parts[1])
                num_questions = min(max(num_questions, 1), 20)  # Limit 1-20
            except ValueError:
                pass
        
        # Get all chunks from notebook for quiz
        chunks = await milvus.get_all_chunks(notebook_id)
        if not chunks:
            # Build chat history with error message
            updated_history = (request.chat_history or []).copy()
            updated_history.append(ChatMessage(role="user", content=request.message))
            error_msg = "❌ Không tìm thấy tài liệu nào trong notebook. Vui lòng upload tài liệu trước."
            updated_history.append(ChatMessage(role="assistant", content=error_msg))

            return ChatResponse(
                message=error_msg,
                sources=[],
                metadata={"command": "quiz", "error": True},
                chat_history=updated_history
            )

        # Generate quiz using MCQ Generator workflow
        questions = await mcq_service.generate_quiz(
            notebook_id=notebook_id,
            num_questions=num_questions,
            difficulty="medium"
        )

        if questions:
            # Save quiz to MongoDB
            now = datetime.now(timezone.utc)
            quiz_doc = {
                "notebook_id": notebook_id,
                "user_id": current_user.id,
                "title": f"Quiz - {notebook_doc['name']}",
                "questions": [q.model_dump() for q in questions],
                "total_questions": len(questions),
                "difficulty": "medium",
                "created_at": now,
                "attempts": 0,
                "best_score": None
            }
            result = mongodb.db.quizzes.insert_one(quiz_doc)
            quiz_id = str(result.inserted_id)

            # Format quiz for display
            quiz_text = f"🎯 **Quiz đã được tạo và lưu!**\n\n"
            quiz_text += f"📝 **{len(questions)} câu hỏi** | ID: `{quiz_id}`\n\n"

            for i, q in enumerate(questions, 1):
                quiz_text += f"**Câu {i}:** {q.question}\n"
                for opt in q.options:
                    quiz_text += f"   {opt}\n"
                quiz_text += f"\n✅ **Đáp án:** {q.correct_answer}\n"
                quiz_text += f"📖 {q.explanation}\n\n---\n\n"

            quiz_text += f"\n💡 *Quiz đã được lưu. Bạn có thể xem lại trong tab Quiz hoặc vào /quiz để tạo quiz mới.*"

            # Build chat history with quiz
            updated_history = (request.chat_history or []).copy()
            updated_history.append(ChatMessage(role="user", content=request.message))
            updated_history.append(ChatMessage(role="assistant", content=quiz_text))

            return ChatResponse(
                message=quiz_text,
                sources=[],
                metadata={"command": "quiz", "quiz_id": quiz_id, "num_questions": len(questions)},
                chat_history=updated_history
            )
        else:
            # Fallback to simple text quiz
            combined_text = "\n\n".join([c["text"] for c in chunks[:30]])
            quiz_content = await llm_service.generate_quiz(
                content=combined_text,
                num_questions=num_questions
            )

            # Build chat history with quiz fallback
            updated_history = (request.chat_history or []).copy()
            updated_history.append(ChatMessage(role="user", content=request.message))
            updated_history.append(ChatMessage(role="assistant", content=quiz_content))

            return ChatResponse(
                message=quiz_content,
                sources=[],
                metadata={"command": "quiz", "num_questions": num_questions},
                chat_history=updated_history
            )
    
    elif message.startswith("/summary"):
        # Parse style (not used in new Summarizer workflow, kept for compatibility)
        parts = message.split()
        style = "detailed"  # default
        if len(parts) > 1 and parts[1] in ["brief", "detailed", "bullet_points"]:
            style = parts[1]

        # Generate notebook summary using Summarizer workflow
        result = await summarizer_service.summarize_notebook(notebook_id=notebook_id)

        if not result.get("overview"):
            error_msg = "❌ Không tìm thấy tài liệu nào trong notebook. Vui lòng upload tài liệu trước."

            # Build chat history with error
            updated_history = (request.chat_history or []).copy()
            updated_history.append(ChatMessage(role="user", content=request.message))
            updated_history.append(ChatMessage(role="assistant", content=error_msg))

            return ChatResponse(
                message=error_msg,
                sources=[],
                metadata={"command": "summary", "error": True},
                chat_history=updated_history
            )

        # Format response
        summary_text = f"📝 **Tóm tắt Notebook**\n\n{result.get('overview', '')}\n\n"

        # Add suggested questions if available
        suggested_questions = result.get("suggested_questions", [])
        if suggested_questions:
            summary_text += "\n💡 **Câu hỏi gợi ý:**\n"
            for i, q in enumerate(suggested_questions, 1):
                summary_text += f"{i}. {q}\n"

        # Add main topics if available
        main_topics = result.get("main_topics", [])
        if main_topics:
            summary_text += f"\n🏷️ **Chủ đề chính:** {', '.join(main_topics[:5])}"

        # Build chat history with summary
        updated_history = (request.chat_history or []).copy()
        updated_history.append(ChatMessage(role="user", content=request.message))
        updated_history.append(ChatMessage(role="assistant", content=summary_text))

        return ChatResponse(
            message=summary_text,
            sources=[],
            metadata={
                "command": "summary",
                "style": style,
                "sources_used": result.get("total_sources", 0),
                "topics": main_topics
            },
            chat_history=updated_history
        )
    
    elif message.startswith("/faq"):
        # Parse number of FAQs
        parts = message.split()
        num_faqs = 5  # default
        if len(parts) > 1:
            try:
                num_faqs = int(parts[1])
                num_faqs = min(max(num_faqs, 1), 20)  # Limit 1-20
            except ValueError:
                pass

        # Generate FAQ using FAQ Generator workflow
        faqs = await faq_service.generate_faq(
            notebook_id=notebook_id,
            num_questions=num_faqs
        )

        if not faqs:
            error_msg = "❌ Không tìm thấy tài liệu nào trong notebook."

            # Build chat history with error
            updated_history = (request.chat_history or []).copy()
            updated_history.append(ChatMessage(role="user", content=request.message))
            updated_history.append(ChatMessage(role="assistant", content=error_msg))

            return ChatResponse(
                message=error_msg,
                sources=[],
                metadata={"command": "faq", "error": True},
                chat_history=updated_history
            )

        # Format FAQ response
        faq_text = f"❓ **Câu hỏi thường gặp** ({len(faqs)} câu)\n\n"

        for i, faq in enumerate(faqs, 1):
            question = faq.get("question", "")
            answer = faq.get("answer", "")
            topic = faq.get("topic", "")

            faq_text += f"**{i}. {question}**\n"
            if topic:
                faq_text += f"   🏷️ *{topic}*\n"
            faq_text += f"   💬 {answer}\n\n"

        faq_text += f"\n💡 *Đã tạo {len(faqs)} câu FAQ từ tài liệu của bạn.*"

        # Build chat history with FAQ
        updated_history = (request.chat_history or []).copy()
        updated_history.append(ChatMessage(role="user", content=request.message))
        updated_history.append(ChatMessage(role="assistant", content=faq_text))

        return ChatResponse(
            message=faq_text,
            sources=[],
            metadata={"command": "faq", "num_questions": len(faqs)},
            chat_history=updated_history
        )
    
    elif message.startswith("/help"):
        help_msg = """📚 **Các lệnh có sẵn:**

- `/quiz [số câu]` - Tạo quiz trắc nghiệm từ tài liệu (mặc định: 5 câu)
- `/summary [style]` - Tóm tắt tài liệu (style: brief, detailed, bullet_points)
- `/faq [số câu]` - Sinh câu hỏi thường gặp (mặc định: 5 câu)
- `/help` - Hiển thị trợ giúp này

**Ví dụ:**
- `/quiz 10` - Tạo 10 câu quiz
- `/summary bullet_points` - Tóm tắt dạng bullet points
- `/faq 3` - Sinh 3 câu FAQ

Hoặc bạn có thể hỏi bất kỳ câu hỏi nào về tài liệu!"""

        # Build chat history with help
        updated_history = (request.chat_history or []).copy()
        updated_history.append(ChatMessage(role="user", content=request.message))
        updated_history.append(ChatMessage(role="assistant", content=help_msg))

        return ChatResponse(
            message=help_msg,
            sources=[],
            metadata={"command": "help"},
            chat_history=updated_history
        )

    else:
        error_msg = "❓ Lệnh không hợp lệ. Gõ `/help` để xem các lệnh có sẵn."

        # Build chat history with error
        updated_history = (request.chat_history or []).copy()
        updated_history.append(ChatMessage(role="user", content=request.message))
        updated_history.append(ChatMessage(role="assistant", content=error_msg))

        return ChatResponse(
            message=error_msg,
            sources=[],
            metadata={"command": "unknown"},
            chat_history=updated_history
        )
