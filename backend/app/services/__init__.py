"""Services Package"""

# Import from shared services
from app.services.shared.embedding_service import EmbeddingService
from app.services.shared.llm_service import LLMService
from app.services.shared.auth_service import AuthService
from app.services.shared.classification_service import ClassificationService
from app.services.shared.web_search_service import WebSearchService

# Import from modules
from app.services.rag.rag_service import RAGService
from app.services.summarizer.summarizer_service import SummarizerService
from app.services.mcq_generator.mcq_service import MCQGeneratorService
from app.services.faq_generator.faq_service import FAQGeneratorService

__all__ = [
    # Shared services
    "EmbeddingService",
    "LLMService",
    "AuthService",
    "ClassificationService",
    "WebSearchService",
    # Module services
    "RAGService",
    "SummarizerService",
    "MCQGeneratorService",
    "FAQGeneratorService",
]