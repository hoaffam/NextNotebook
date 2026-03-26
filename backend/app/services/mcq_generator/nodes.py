"""
MCQ Generator Workflow Nodes
Node functions for the MCQ Generator LangGraph workflow
"""

import json
import uuid
from typing import Dict, Any, List
from app.services.mcq_generator.state import MCQGeneratorState
from app.services.mcq_generator.question_bank import (
    MCQ_GENERATION_PROMPT,
    MCQ_GENERATOR_SYSTEM,
    DIFFICULTY_GUIDELINES,
    VALIDATION_CRITERIA
)
from app.database.milvus_client import MilvusService
from app.services.shared.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class MCQGeneratorNodes:
    """Node functions for MCQ Generator workflow"""

    def __init__(
        self,
        milvus_service: MilvusService,
        llm_service: LLMService
    ):
        """
        Initialize nodes with dependencies

        Args:
            milvus_service: Milvus service for vector search
            llm_service: LLM service for generation
        """
        self.milvus = milvus_service
        self.llm = llm_service

    async def retrieve_chunks(self, state: MCQGeneratorState) -> Dict[str, Any]:
        """
        Retrieve all chunks from Milvus

        Args:
            state: Current workflow state

        Returns:
            Partial state with all_chunks
        """
        logger.info(f"[MCQGenerator] Retrieving chunks for notebook_id={state['notebook_id']}")

        try:
            chunks = await self.milvus.get_all_chunks(state["notebook_id"])

            logger.info(f"[MCQGenerator] Retrieved {len(chunks)} chunks")

            return {
                "all_chunks": chunks,
                "chunk_count": len(chunks),
                "steps": ["retrieve_chunks"]
            }

        except Exception as e:
            logger.error(f"[MCQGenerator] Failed to retrieve chunks: {e}")
            return {
                "all_chunks": [],
                "chunk_count": 0,
                "steps": ["retrieve_chunks (failed)"]
            }

    async def diversity_sampling(self, state: MCQGeneratorState) -> Dict[str, Any]:
        """
        Select diverse chunks for better question coverage

        Args:
            state: Current workflow state

        Returns:
            Partial state with selected_chunks and combined_text
        """
        logger.info("[MCQGenerator] Performing diversity sampling")

        chunks = state.get("all_chunks", [])
        num_questions = state.get("num_questions", 10)

        # Select 2x chunks per question for diversity
        target_count = min(num_questions * 2, len(chunks))

        selected_chunks = self._select_diverse_chunks(chunks, target_count)

        # Combine text
        combined_text = "\n\n".join([c.get("text", "") for c in selected_chunks])

        # Calculate diversity score (simple: ratio of selected to total)
        diversity_score = len(selected_chunks) / len(chunks) if chunks else 0.0

        logger.info(f"[MCQGenerator] Selected {len(selected_chunks)} chunks (diversity: {diversity_score:.2f})")

        return {
            "selected_chunks": selected_chunks,
            "combined_text": combined_text,
            "chunk_diversity_score": diversity_score,
            "steps": ["diversity_sampling"]
        }

    async def batch_generate(self, state: MCQGeneratorState) -> Dict[str, Any]:
        """
        Generate questions using LLM

        Args:
            state: Current workflow state

        Returns:
            Partial state with raw_questions
        """
        logger.info("[MCQGenerator] Generating questions with LLM")

        combined_text = state.get("combined_text", "")
        num_questions = state.get("num_questions", 10)
        difficulty = state.get("difficulty", "medium")

        if not combined_text:
            logger.warning("[MCQGenerator] No text to generate questions from")
            return {
                "raw_questions": [],
                "steps": ["batch_generate (no text)"]
            }

        try:
            # Truncate text if too long (max 15000 chars)
            truncated_text = combined_text[:15000]

            # Build prompt
            difficulty_guide = DIFFICULTY_GUIDELINES.get(difficulty, "")
            prompt = MCQ_GENERATION_PROMPT.format(
                num_questions=num_questions,
                difficulty=difficulty.capitalize(),
                text=truncated_text
            ) + "\n\n" + difficulty_guide

            messages = [
                {"role": "system", "content": MCQ_GENERATOR_SYSTEM},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm.chat(messages, temperature=0.7, max_tokens=2000)

            # Parse JSON response
            raw_questions = self._parse_json_array(response)

            logger.info(f"[MCQGenerator] Generated {len(raw_questions)} raw questions")

            return {
                "raw_questions": raw_questions,
                "steps": ["batch_generate"]
            }

        except Exception as e:
            logger.error(f"[MCQGenerator] Failed to generate questions: {e}")
            return {
                "raw_questions": [],
                "steps": ["batch_generate (failed)"]
            }

    async def validate_questions(self, state: MCQGeneratorState) -> Dict[str, Any]:
        """
        Validate and filter questions

        Args:
            state: Current workflow state

        Returns:
            Partial state with validated questions
        """
        logger.info("[MCQGenerator] Validating questions")

        raw_questions = state.get("raw_questions", [])
        valid_questions = []

        for q in raw_questions:
            if self._is_valid_question(q):
                valid_questions.append(q)
            else:
                logger.warning(f"[MCQGenerator] Invalid question filtered: {q.get('question', 'N/A')[:50]}")

        logger.info(f"[MCQGenerator] Validated {len(valid_questions)}/{len(raw_questions)} questions")

        return {
            "raw_questions": valid_questions,
            "steps": ["validate_questions"]
        }

    async def format_output(self, state: MCQGeneratorState) -> Dict[str, Any]:
        """
        Format questions with IDs and metadata

        Args:
            state: Current workflow state

        Returns:
            Partial state with final questions
        """
        logger.info("[MCQGenerator] Formatting output")

        raw_questions = state.get("raw_questions", [])
        difficulty = state.get("difficulty", "medium")

        formatted_questions = []

        for q in raw_questions:
            formatted_questions.append({
                "id": str(uuid.uuid4()),
                "question": q.get("question", ""),
                "options": q.get("options", []),
                "correct_answer": q.get("correct_answer", "A"),
                "explanation": q.get("explanation", ""),
                "difficulty": difficulty
            })

        logger.info(f"[MCQGenerator] Formatted {len(formatted_questions)} questions")

        return {
            "questions": formatted_questions,
            "total_generated": len(formatted_questions),
            "steps": ["format_output"]
        }

    def _select_diverse_chunks(self, chunks: List[Dict], count: int) -> List[Dict]:
        """
        Select diverse chunks at regular intervals

        Args:
            chunks: All available chunks
            count: Number of chunks to select

        Returns:
            Selected chunks
        """
        if len(chunks) <= count:
            return chunks

        # Simple strategy: take chunks at regular intervals
        step = len(chunks) // count
        selected = []

        for i in range(0, len(chunks), step):
            if len(selected) >= count:
                break
            selected.append(chunks[i])

        return selected

    def _parse_json_array(self, response: str) -> List[Dict]:
        """
        Parse JSON array from LLM response

        Args:
            response: LLM response text

        Returns:
            Parsed list of dicts or empty list
        """
        try:
            # Try to extract JSON array from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
            else:
                logger.warning("No JSON array found in response")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return []

    def _is_valid_question(self, question: Dict) -> bool:
        """
        Validate a single question

        Args:
            question: Question dict to validate

        Returns:
            True if valid, False otherwise
        """
        criteria = VALIDATION_CRITERIA

        # Check required fields
        for field in criteria["required_fields"]:
            if field not in question:
                return False

        # Check options count
        options = question.get("options", [])
        if len(options) != criteria["options_count"]:
            return False

        # Check correct answer
        correct_answer = question.get("correct_answer", "")
        if correct_answer not in criteria["valid_answers"]:
            return False

        # Check minimum lengths
        question_text = question.get("question", "")
        explanation = question.get("explanation", "")
        if len(question_text) < criteria["min_question_length"]:
            return False
        if len(explanation) < criteria["min_explanation_length"]:
            return False

        return True
