"""
Embedding Service
Generate text embeddings using Google Gemini
"""

from typing import List
import google.generativeai as genai

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingService:
    """Generate embeddings using Google Gemini API"""

    def __init__(self):
        """Initialize Gemini client"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )

            return result['embedding']

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            all_embeddings = []

            # Gemini can handle batch embedding
            for i, text in enumerate(texts):
                result = genai.embed_content(
                    model=self.model,
                    content=text,
                    task_type="retrieval_document"
                )
                all_embeddings.append(result['embedding'])

                if (i + 1) % 10 == 0:
                    logger.debug(f"Generated embeddings: {i + 1}/{len(texts)}")

            logger.info(f"Generated {len(all_embeddings)} embeddings")
            return all_embeddings

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query
        Uses retrieval_query task type for better search results
        """
        try:
            result = genai.embed_content(
                model=self.model,
                content=query,
                task_type="retrieval_query"
            )

            return result['embedding']

        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise


# Singleton instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get singleton EmbeddingService instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
