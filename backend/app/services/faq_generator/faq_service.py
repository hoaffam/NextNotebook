"""
FAQ Generator Service
High-level service wrapper for the FAQ Generator workflow
"""

from typing import List, Dict, Any
from app.services.faq_generator.workflow import create_faq_workflow
from app.database.milvus_client import MilvusService
from app.services.shared.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class FAQGeneratorService:
    """High-level FAQ Generator service"""

    def __init__(
        self,
        milvus_service: MilvusService,
        llm_service: LLMService
    ):
        """
        Initialize FAQ Generator service with dependencies

        Args:
            milvus_service: Milvus vector database service
            llm_service: LLM service
        """
        self.milvus = milvus_service
        self.llm = llm_service

        # Create workflow
        self.workflow = create_faq_workflow(
            milvus_service=milvus_service,
            llm_service=llm_service
        )

        logger.info("FAQ Generator Service initialized")

    async def generate_faq(
        self,
        notebook_id: str,
        num_questions: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generate FAQ from notebook content

        Args:
            notebook_id: Source notebook ID
            num_questions: Number of FAQ pairs to generate

        Returns:
            List of FAQ dicts with {question, answer, topic}
        """
        try:
            # Initial state
            initial_state = {
                "notebook_id": notebook_id,
                "num_questions": num_questions,
                "all_chunks": [],
                "combined_text": "",
                "detected_topics": [],
                "topic_type": "single",
                "raw_faqs": [],
                "faqs": [],
                "total_generated": 0,
                "steps": [],
                "topic_count": 0,
                "chunk_count": 0
            }

            # Run workflow
            result = await self.workflow.ainvoke(initial_state)

            logger.info(f"FAQ generation completed: {result.get('steps', [])}")

            faqs = result.get("faqs", [])

            logger.info(f"Generated {len(faqs)} FAQs")

            return faqs

        except Exception as e:
            logger.error(f"FAQ generation failed: {e}")
            import traceback
            traceback.print_exc()
            return []


# Singleton instance
_faq_service = None


def get_faq_service(
    milvus_service: MilvusService = None,
    llm_service: LLMService = None
) -> FAQGeneratorService:
    """Get singleton FAQ Generator service instance"""
    global _faq_service

    if _faq_service is None:
        # Import here to avoid circular dependencies
        from app.api.deps import (
            get_milvus_service,
            get_llm_service
        )

        _faq_service = FAQGeneratorService(
            milvus_service=milvus_service or get_milvus_service(),
            llm_service=llm_service or get_llm_service()
        )

    return _faq_service
