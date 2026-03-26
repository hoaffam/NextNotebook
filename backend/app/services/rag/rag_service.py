"""
RAG Service
High-level service wrapper for the RAG (CRAG) workflow
"""

from typing import Dict, List, Any
from app.services.rag.workflow import create_rag_workflow
from app.services.shared.lexical_service import LexicalBM25Service
from app.database.milvus_client import MilvusService
from app.services.shared.embedding_service import EmbeddingService
from app.services.shared.llm_service import LLMService
from app.services.shared.web_search_service import WebSearchService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RAGService:
    """High-level RAG service for chat/Q&A"""

    def __init__(
        self,
        milvus_service: MilvusService,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        web_search_service: WebSearchService
    ):
        """
        Initialize RAG service with dependencies

        Args:
            milvus_service: Milvus vector database service
            embedding_service: Text embedding service
            llm_service: LLM service
            web_search_service: Web search service
        """
        self.milvus = milvus_service
        self.embedding = embedding_service
        self.llm = llm_service
        self.web_search = web_search_service

        # Create workflow
        lexical_service = LexicalBM25Service(milvus_service)

        self.workflow = create_rag_workflow(
            milvus_service=milvus_service,
            embedding_service=embedding_service,
            llm_service=llm_service,
            web_search_service=web_search_service,
            lexical_service=lexical_service
        )

        logger.info("RAG Service initialized")

    async def chat(
        self,
        question: str,
        notebook_id: str,
        chat_history: List[Dict] = None,
        enable_web_search: bool = False
    ) -> Dict[str, Any]:
        """
        Chat with documents using RAG workflow

        Args:
            question: User question
            notebook_id: Notebook ID to query
            chat_history: Previous chat messages
            enable_web_search: Force web search

        Returns:
            Dict with answer, sources, and web_sources
        """
        try:
            # Initial state
            initial_state = {
                "question": question,
                "notebook_id": notebook_id,
                "chat_history": chat_history or [],
                "documents": [],
                "filtered_documents": [],
                "rewritten_question": None,
                "web_search_needed": False,
                "force_web_search": enable_web_search,  # User toggle
                "web_results": [],
                "answer": "",
                "sources": [],
                "web_sources": [],
                "steps": [],
                "retrieval_count": 0,
                "used_web_search": False,
                # Quality signals (will be set/updated in nodes.grade_documents)
                "coverage_score": 0.0,
                "answerable": False,
                "citable": False,
            }

            # Run workflow
            result = await self.workflow.ainvoke(initial_state)

            logger.info(f"RAG workflow completed: {result.get('steps', [])}")

            return {
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "web_sources": result.get("web_sources", []),
                "used_web_search": result.get("used_web_search", False),
                "steps": result.get("steps", [])
            }

        except Exception as e:
            logger.error(f"RAG chat failed: {e}")
            raise


# Singleton instance
_rag_service = None


def get_rag_service(
    milvus_service: MilvusService = None,
    embedding_service: EmbeddingService = None,
    llm_service: LLMService = None,
    web_search_service: WebSearchService = None
) -> RAGService:
    """Get singleton RAG service instance"""
    global _rag_service

    if _rag_service is None:
        # Import here to avoid circular dependencies
        from app.api.deps import (
            get_milvus_service,
            get_embedding_service,
            get_llm_service,
            get_web_search_service
        )

        _rag_service = RAGService(
            milvus_service=milvus_service or get_milvus_service(),
            embedding_service=embedding_service or get_embedding_service(),
            llm_service=llm_service or get_llm_service(),
            web_search_service=web_search_service or get_web_search_service()
        )

    return _rag_service
