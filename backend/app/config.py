"""
Application Configuration
Load settings from environment variables
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Settings
    APP_NAME: str = "NotebookLM Clone"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # LLM Provider Selection
    LLM_PROVIDER: Literal["groq", "xai", "gemini", "openai"] = "groq"
    
    # Groq Settings (FREE tier - 30 req/min)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # xAI (Grok) Settings
    XAI_API_KEY: Optional[str] = None
    XAI_MODEL: str = "grok-beta"
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    
    # Google Gemini Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    
    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_BASE_URL: Optional[str] = None
    
    # Zilliz Cloud Settings
    ZILLIZ_CLOUD_URI: str
    ZILLIZ_CLOUD_TOKEN: str
    ZILLIZ_DB_NAME: Optional[str] = None
    ZILLIZ_PASSWORD: Optional[str] = None
    ZILLIZ_COLLECTION_NAME: str = "documents"
    
    # Vector Settings
    EMBEDDING_DIMENSION: int = 768  # Gemini text-embedding-004 dimension
    
    # Chunking Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Search Settings
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.3  # Lowered for COSINE distance in Milvus
    
    # File Upload Settings
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = ["pdf", "docx", "txt"]
    UPLOAD_DIR: str = "uploads"
    
    # Web Search Settings (optional)
    TAVILY_API_KEY: Optional[str] = None  # Tavily for web search
    SERPAPI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None
    
    # Classification Settings
    CLASSIFICATION_THRESHOLD: float = 0.45
    MAX_CATEGORY_LABELS: int = 3
    
    # Summary Settings
    SUMMARY_MAX_LENGTH: int = 500

    # Input Guardrails
    ENABLE_INPUT_GUARDRAILS: bool = True
    ENABLE_INPUT_SAFETY: bool = True
    MAX_INPUT_LENGTH: int = 2000
    MIN_INPUT_LENGTH: int = 2

    # Query Routing
    ENABLE_INTELLIGENT_ROUTING: bool = True
    ROUTING_LLM_TEMPERATURE: float = 0.2
    
    # MongoDB Settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "notebooklm"
    
    # JWT Authentication Settings
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production-abc123xyz789"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()
