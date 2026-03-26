"""
Shared Services Module
Contains services used across multiple modules
"""

from app.services.shared.llm_service import LLMService, get_llm_service
from app.services.shared.embedding_service import EmbeddingService, get_embedding_service
from app.services.shared.auth_service import AuthService, get_auth_service
from app.services.shared.classification_service import (
    ClassificationService,
    get_classification_service
)
from app.services.shared.web_search_service import (
    WebSearchService,
    get_web_search_service
)

__all__ = [
    "LLMService",
    "get_llm_service",
    "EmbeddingService",
    "get_embedding_service",
    "AuthService",
    "get_auth_service",
    "ClassificationService",
    "get_classification_service",
    "WebSearchService",
    "get_web_search_service",
]
