"""
Summarizer Service
High-level service wrapper for the Summarizer workflow
"""

from typing import Dict, List, Any, Optional
from bson import ObjectId
from app.services.summarizer.workflow import create_summarizer_workflow
from app.database.mongodb_client import MongoDBClient
from app.database.milvus_client import MilvusService
from app.services.shared.llm_service import LLMService
from app.services.shared.embedding_service import EmbeddingService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SummarizerService:
    """High-level Summarizer service"""

    def __init__(
        self,
        mongodb_client: MongoDBClient,
        milvus_service: MilvusService,
        llm_service: LLMService,
        embedding_service: EmbeddingService
    ):
        """
        Initialize Summarizer service with dependencies

        Args:
            mongodb_client: MongoDB client
            milvus_service: Milvus vector database service
            llm_service: LLM service
            embedding_service: Text embedding service
        """
        self.mongodb = mongodb_client
        self.milvus = milvus_service
        self.llm = llm_service
        self.embedding = embedding_service

        # Create workflow
        self.workflow = create_summarizer_workflow(
            mongodb_client=mongodb_client,
            milvus_service=milvus_service,
            llm_service=llm_service,
            embedding_service=embedding_service
        )

        logger.info("Summarizer Service initialized")

    async def summarize_document(
        self,
        document_id: str,
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        Generate summary for a single document

        Args:
            document_id: Document ID to summarize
            max_length: Maximum summary length in characters

        Returns:
            Dict with summary, key_topics, and summary_embedding
        """
        try:
            # Get document to find notebook_id
            doc = self.mongodb.documents.find_one({"_id": ObjectId(document_id)})
            if not doc:
                logger.error(f"Document {document_id} not found")
                return {
                    "summary": "Document not found.",
                    "key_topics": [],
                    "summary_embedding": None
                }

            # Initial state
            initial_state = {
                "notebook_id": doc.get("notebook_id", ""),
                "document_id": document_id,
                "style": "document",
                "max_length": max_length,
                "documents": [],
                "chunks": [],
                "selected_text": "",
                "all_summaries": [],
                "summary": "",
                "key_topics": [],
                "suggested_questions": [],
                "summary_embedding": None,
                "sources_used": 0,
                "steps": [],
                "document_count": 0
            }

            # Run workflow
            result = await self.workflow.ainvoke(initial_state)

            logger.info(f"Document summarization completed: {result.get('steps', [])}")

            return {
                "summary": result.get("summary", ""),
                "key_topics": result.get("key_topics", []),
                "summary_embedding": result.get("summary_embedding", None)
            }

        except Exception as e:
            logger.error(f"Document summarization failed: {e}")
            return {
                "summary": f"Failed to generate summary: {str(e)}",
                "key_topics": [],
                "summary_embedding": None
            }

    async def summarize_notebook(
        self,
        notebook_id: str
    ) -> Dict[str, Any]:
        """
        Generate overview for entire notebook

        Args:
            notebook_id: Notebook ID to summarize

        Returns:
            Dict with overview, suggested_questions, main_topics, and documents
        """
        try:
            # Initial state
            initial_state = {
                "notebook_id": notebook_id,
                "document_id": None,
                "style": "notebook",
                "max_length": None,
                "documents": [],
                "chunks": [],
                "selected_text": "",
                "all_summaries": [],
                "summary": "",
                "key_topics": [],
                "suggested_questions": [],
                "summary_embedding": None,
                "sources_used": 0,
                "steps": [],
                "document_count": 0
            }

            # Run workflow
            result = await self.workflow.ainvoke(initial_state)

            logger.info(f"Notebook summarization completed: {result.get('steps', [])}")

            # Build response with document details
            documents = result.get("documents", [])
            document_details = [
                {
                    "id": doc.get("id", ""),
                    "filename": doc.get("filename", ""),
                    "summary": doc.get("summary", ""),
                    "key_topics": doc.get("key_topics", []),
                    "categories": doc.get("categories", [])
                }
                for doc in documents
            ]

            return {
                "overview": result.get("summary", ""),
                "suggested_questions": result.get("suggested_questions", []),
                "total_sources": result.get("sources_used", 0),
                "main_topics": result.get("key_topics", []),
                "documents": document_details
            }

        except Exception as e:
            logger.error(f"Notebook summarization failed: {e}")
            return {
                "overview": f"Failed to generate overview: {str(e)}",
                "suggested_questions": [],
                "total_sources": 0,
                "main_topics": [],
                "documents": []
            }

    async def generate_document_summary(
        self,
        text: str,
        filename: str,
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility
        Generate summary directly from text (used in document upload flow)

        Args:
            text: Full document text
            filename: Name of the document
            max_length: Maximum summary length

        Returns:
            Dict with summary, key_topics, and summary_embedding
        """
        try:
            from app.services.summarizer.strategies import DOCUMENT_SUMMARY_PROMPT, DOCUMENT_ANALYZER_SYSTEM
            import json

            # Truncate text
            truncated_text = text[:15000] if len(text) > 15000 else text

            # Build prompt
            prompt = DOCUMENT_SUMMARY_PROMPT.format(
                filename=filename,
                text=truncated_text
            )

            messages = [
                {"role": "system", "content": DOCUMENT_ANALYZER_SYSTEM},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm.chat(messages, temperature=0.3, max_tokens=1000)

            # Parse JSON
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    result = json.loads(response[json_start:json_end])
                else:
                    raise ValueError("No JSON found")
            except (json.JSONDecodeError, ValueError):
                logger.warning("Failed to parse JSON summary, using fallback")
                result = {
                    "summary": response[:max_length],
                    "key_topics": []
                }

            summary = result.get("summary", "")[:max_length]
            key_topics = result.get("key_topics", [])

            # Generate embedding
            summary_embedding = await self.embedding.embed_text(summary)

            logger.info(f"Generated summary for {filename}: {len(summary)} chars, {len(key_topics)} topics")

            return {
                "summary": summary,
                "key_topics": key_topics,
                "summary_embedding": summary_embedding
            }

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {
                "summary": f"Document: {filename}",
                "key_topics": [],
                "summary_embedding": None
            }

    async def generate_notebook_overview(
        self,
        documents: List[Dict],
        notebook_name: str
    ) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility
        Generate overview directly from document list

        Args:
            documents: List of documents with their summaries
            notebook_name: Name of the notebook

        Returns:
            Dict with overview, suggested_questions, and metadata
        """
        try:
            from app.services.summarizer.strategies import NOTEBOOK_OVERVIEW_PROMPT, RESEARCH_ASSISTANT_SYSTEM
            import json

            if not documents:
                return {
                    "overview": "Notebook này chưa có tài liệu nào. Hãy upload tài liệu để bắt đầu!",
                    "suggested_questions": [],
                    "total_sources": 0,
                    "main_topics": []
                }

            # Combine summaries
            summaries_text = "\n\n".join([
                f"📄 {doc.get('filename', 'Unknown')}:\n{doc.get('summary', 'No summary')}"
                for doc in documents
            ])

            # Collect topics
            all_topics = []
            for doc in documents:
                all_topics.extend(doc.get("key_topics", []))
            unique_topics = list(set(all_topics))[:10]

            # Build prompt
            prompt = NOTEBOOK_OVERVIEW_PROMPT.format(
                notebook_name=notebook_name,
                summaries_text=summaries_text
            )

            messages = [
                {"role": "system", "content": RESEARCH_ASSISTANT_SYSTEM},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm.chat(messages, temperature=0.3, max_tokens=800)

            # Parse JSON
            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    result = json.loads(response[json_start:json_end])
                else:
                    raise ValueError("No JSON found")
            except (json.JSONDecodeError, ValueError):
                result = {
                    "overview": response,
                    "suggested_questions": []
                }

            return {
                "overview": result.get("overview", ""),
                "suggested_questions": result.get("suggested_questions", []),
                "total_sources": len(documents),
                "main_topics": unique_topics,
                "documents": [
                    {
                        "id": doc.get("id", ""),
                        "filename": doc.get("filename", ""),
                        "summary": doc.get("summary", ""),
                        "key_topics": doc.get("key_topics", []),
                        "categories": doc.get("categories", [])
                    }
                    for doc in documents
                ]
            }

        except Exception as e:
            logger.error(f"Failed to generate notebook overview: {e}")
            return {
                "overview": f"Notebook chứa {len(documents)} tài liệu.",
                "suggested_questions": [],
                "total_sources": len(documents),
                "main_topics": [],
                "documents": []
            }


# Singleton instance
_summarizer_service = None


def get_summarizer_service(
    mongodb_client: MongoDBClient = None,
    milvus_service: MilvusService = None,
    llm_service: LLMService = None,
    embedding_service: EmbeddingService = None
) -> SummarizerService:
    """Get singleton Summarizer service instance"""
    global _summarizer_service

    if _summarizer_service is None:
        # Import here to avoid circular dependencies
        from app.api.deps import (
            get_milvus_service,
            get_llm_service,
            get_embedding_service
        )
        from app.database.mongodb_client import get_mongodb

        _summarizer_service = SummarizerService(
            mongodb_client=mongodb_client or get_mongodb(),
            milvus_service=milvus_service or get_milvus_service(),
            llm_service=llm_service or get_llm_service(),
            embedding_service=embedding_service or get_embedding_service()
        )

    return _summarizer_service
