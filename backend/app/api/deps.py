"""
API Dependencies
Shared dependencies for API routes
"""

from typing import Generator
from app.config import settings
from app.database.milvus_client import MilvusService
from app.services.shared.embedding_service import EmbeddingService, get_embedding_service as _get_embedding_service
from app.services.shared.llm_service import LLMService, get_llm_service as _get_llm_service
from app.services.shared.web_search_service import WebSearchService, get_web_search_service as _get_web_search_service
from app.services.shared.classification_service import ClassificationService, get_classification_service as _get_classification_service
from app.services.summarizer.summarizer_service import SummarizerService, get_summarizer_service as _get_summarizer_service
from app.services.mcq_generator.mcq_service import MCQGeneratorService, get_mcq_service as _get_mcq_service
from app.services.faq_generator.faq_service import FAQGeneratorService, get_faq_service as _get_faq_service
from app.services.shared.input_guardrails import InputGuardrailsService
from app.services.shared.query_router import QueryRouter
from app.services.shared.simple_response_handler import SimpleResponseHandler


# Dependency instances (lazy initialization)
_milvus_service = None
_input_guardrails_service = None
_query_router_service = None
_simple_response_handler = None


def get_milvus_service() -> MilvusService:
    """Get Milvus service instance"""
    global _milvus_service
    if _milvus_service is None:
        _milvus_service = MilvusService()
    return _milvus_service


def get_embedding_service() -> EmbeddingService:
    """Get Embedding service instance"""
    return _get_embedding_service()


def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    return _get_llm_service()


def get_web_search_service() -> WebSearchService:
    """Get Web Search service instance"""
    return _get_web_search_service()


def get_classification_service() -> ClassificationService:
    """Get Classification service instance"""
    return _get_classification_service()


def get_summarizer_service() -> SummarizerService:
    """Get Summarizer service instance"""
    return _get_summarizer_service()


def get_mcq_service() -> MCQGeneratorService:
    """Get MCQ Generator service instance"""
    return _get_mcq_service()


def get_faq_service() -> FAQGeneratorService:
    """Get FAQ Generator service instance"""
    return _get_faq_service()


def get_input_guardrails_service() -> InputGuardrailsService:
    """Get Input Guardrails service instance"""
    global _input_guardrails_service
    if _input_guardrails_service is None:
        _input_guardrails_service = InputGuardrailsService(llm_service=get_llm_service())
    return _input_guardrails_service


def get_query_router_service() -> QueryRouter:
    """Get Query Router service instance"""
    global _query_router_service
    if _query_router_service is None:
        _query_router_service = QueryRouter(llm_service=get_llm_service())
    return _query_router_service


def get_simple_response_handler() -> SimpleResponseHandler:
    """Get Simple Response Handler instance"""
    global _simple_response_handler
    if _simple_response_handler is None:
        _simple_response_handler = SimpleResponseHandler(llm_service=get_llm_service())
    return _simple_response_handler
