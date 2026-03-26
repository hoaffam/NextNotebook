"""
MCQ Generator Service
High-level service wrapper for the MCQ Generator workflow
"""

from typing import List, Dict, Any
from app.services.mcq_generator.workflow import create_mcq_workflow
from app.database.milvus_client import MilvusService
from app.services.shared.llm_service import LLMService
from app.models.quiz import QuizQuestion
from app.utils.logger import setup_logger
import uuid

logger = setup_logger(__name__)


class MCQGeneratorService:
    """High-level MCQ Generator service"""

    def __init__(
        self,
        milvus_service: MilvusService,
        llm_service: LLMService
    ):
        """
        Initialize MCQ Generator service with dependencies

        Args:
            milvus_service: Milvus vector database service
            llm_service: LLM service
        """
        self.milvus = milvus_service
        self.llm = llm_service

        # Create workflow
        self.workflow = create_mcq_workflow(
            milvus_service=milvus_service,
            llm_service=llm_service
        )

        logger.info("MCQ Generator Service initialized")

    async def generate_quiz(
        self,
        notebook_id: str,
        num_questions: int = 10,
        difficulty: str = "medium"
    ) -> List[QuizQuestion]:
        """
        Generate quiz questions from notebook documents

        Args:
            notebook_id: Source notebook ID
            num_questions: Number of questions to generate
            difficulty: Question difficulty (easy, medium, hard)

        Returns:
            List of QuizQuestion objects
        """
        try:
            # Initial state
            initial_state = {
                "notebook_id": notebook_id,
                "num_questions": num_questions,
                "difficulty": difficulty,
                "all_chunks": [],
                "selected_chunks": [],
                "combined_text": "",
                "raw_questions": [],
                "questions": [],
                "total_generated": 0,
                "steps": [],
                "chunk_diversity_score": 0.0,
                "chunk_count": 0
            }

            # Run workflow
            result = await self.workflow.ainvoke(initial_state)

            logger.info(f"MCQ generation completed: {result.get('steps', [])}")

            # Convert to QuizQuestion format
            questions = []
            for q in result.get("questions", []):
                questions.append(QuizQuestion(
                    id=q.get("id", str(uuid.uuid4())),
                    question=q.get("question", ""),
                    options=q.get("options", []),
                    correct_answer=q.get("correct_answer", "A"),
                    explanation=q.get("explanation", ""),
                    difficulty=q.get("difficulty", difficulty)
                ))

            logger.info(f"Generated {len(questions)} quiz questions")

            return questions

        except Exception as e:
            logger.error(f"MCQ generation failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def generate_questions_legacy(
        self,
        notebook_id: str,
        num_questions: int = 10,
        difficulty: str = "medium"
    ) -> List[Dict]:
        """
        Legacy method for backward compatibility
        Returns raw dict format instead of QuizQuestion objects

        Args:
            notebook_id: Source notebook ID
            num_questions: Number of questions to generate
            difficulty: Question difficulty

        Returns:
            List of question dicts
        """
        questions = await self.generate_quiz(notebook_id, num_questions, difficulty)

        # Convert QuizQuestion objects to dicts
        return [
            {
                "id": q.id,
                "question": q.question,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty
            }
            for q in questions
        ]


# Singleton instance
_mcq_service = None


def get_mcq_service(
    milvus_service: MilvusService = None,
    llm_service: LLMService = None
) -> MCQGeneratorService:
    """Get singleton MCQ Generator service instance"""
    global _mcq_service

    if _mcq_service is None:
        # Import here to avoid circular dependencies
        from app.api.deps import (
            get_milvus_service,
            get_llm_service
        )

        _mcq_service = MCQGeneratorService(
            milvus_service=milvus_service or get_milvus_service(),
            llm_service=llm_service or get_llm_service()
        )

    return _mcq_service
