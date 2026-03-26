"""
FAQ Generator Workflow Nodes
Node functions for the FAQ Generator LangGraph workflow
"""

import json
from typing import Dict, Any, List
from app.services.faq_generator.state import FAQGeneratorState
from app.services.faq_generator.prompts import (
    TOPIC_EXTRACTION_PROMPT,
    SINGLE_TOPIC_FAQ_PROMPT,
    MULTI_TOPIC_FAQ_PROMPT,
    TOPIC_ANALYZER_SYSTEM,
    FAQ_GENERATOR_SYSTEM
)
from app.database.milvus_client import MilvusService
from app.services.shared.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class FAQGeneratorNodes:
    """Node functions for FAQ Generator workflow"""

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

    async def retrieve_chunks(self, state: FAQGeneratorState) -> Dict[str, Any]:
        """
        Retrieve all chunks from Milvus

        Args:
            state: Current workflow state

        Returns:
            Partial state with all_chunks
        """
        logger.info(f"[FAQGenerator] Retrieving chunks for notebook_id={state['notebook_id']}")

        try:
            chunks = await self.milvus.get_all_chunks(state["notebook_id"])

            # Combine chunks (limit to 30 for FAQ generation)
            selected_chunks = chunks[:30] if len(chunks) > 30 else chunks
            combined_text = "\n\n".join([c.get("text", "") for c in selected_chunks])

            logger.info(f"[FAQGenerator] Retrieved {len(chunks)} chunks, using {len(selected_chunks)}")

            return {
                "all_chunks": chunks,
                "combined_text": combined_text,
                "chunk_count": len(chunks),
                "steps": ["retrieve_chunks"]
            }

        except Exception as e:
            logger.error(f"[FAQGenerator] Failed to retrieve chunks: {e}")
            return {
                "all_chunks": [],
                "combined_text": "",
                "chunk_count": 0,
                "steps": ["retrieve_chunks (failed)"]
            }

    async def topic_extraction(self, state: FAQGeneratorState) -> Dict[str, Any]:
        """
        Extract topics and classify as single/multi topic

        Args:
            state: Current workflow state

        Returns:
            Partial state with detected_topics and topic_type
        """
        logger.info("[FAQGenerator] Extracting topics")

        combined_text = state.get("combined_text", "")

        if not combined_text:
            logger.warning("[FAQGenerator] No text to extract topics from")
            return {
                "detected_topics": [],
                "topic_type": "single",
                "topic_count": 0,
                "steps": ["topic_extraction (no text)"]
            }

        try:
            # Truncate text if too long
            truncated_text = combined_text[:10000]

            # Build prompt
            prompt = TOPIC_EXTRACTION_PROMPT.format(text=truncated_text)

            messages = [
                {"role": "system", "content": TOPIC_ANALYZER_SYSTEM},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm.chat(messages, temperature=0.3, max_tokens=500)

            # Parse JSON response
            result = self._parse_json_object(response)

            detected_topics = result.get("topics", [])
            topic_type = result.get("topic_type", "single")

            # Fallback: if 1-2 topics → single, else → multi
            if not topic_type or topic_type not in ["single", "multi"]:
                topic_type = "single" if len(detected_topics) <= 2 else "multi"

            logger.info(f"[FAQGenerator] Detected {len(detected_topics)} topics, type: {topic_type}")

            return {
                "detected_topics": detected_topics,
                "topic_type": topic_type,
                "topic_count": len(detected_topics),
                "steps": ["topic_extraction"]
            }

        except Exception as e:
            logger.error(f"[FAQGenerator] Failed to extract topics: {e}")
            return {
                "detected_topics": [],
                "topic_type": "single",
                "topic_count": 0,
                "steps": ["topic_extraction (failed)"]
            }

    async def generate_focused_faq(self, state: FAQGeneratorState) -> Dict[str, Any]:
        """
        Generate FAQ for single-topic content

        Args:
            state: Current workflow state

        Returns:
            Partial state with raw_faqs
        """
        logger.info("[FAQGenerator] Generating focused FAQ (single topic)")

        combined_text = state.get("combined_text", "")
        num_questions = state.get("num_questions", 5)
        detected_topics = state.get("detected_topics", [])
        main_topic = detected_topics[0] if detected_topics else "this topic"

        if not combined_text:
            logger.warning("[FAQGenerator] No text to generate FAQ from")
            return {
                "raw_faqs": [],
                "steps": ["generate_focused_faq (no text)"]
            }

        try:
            # Truncate text
            truncated_text = combined_text[:10000]

            # Build prompt
            prompt = SINGLE_TOPIC_FAQ_PROMPT.format(
                main_topic=main_topic,
                num_questions=num_questions,
                text=truncated_text
            )

            messages = [
                {"role": "system", "content": FAQ_GENERATOR_SYSTEM},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm.chat(messages, temperature=0.7, max_tokens=1500)

            # Parse JSON array
            raw_faqs = self._parse_json_array(response)

            # Add topic to each FAQ
            for faq in raw_faqs:
                if "topic" not in faq:
                    faq["topic"] = main_topic

            logger.info(f"[FAQGenerator] Generated {len(raw_faqs)} FAQs")

            return {
                "raw_faqs": raw_faqs,
                "steps": ["generate_focused_faq"]
            }

        except Exception as e:
            logger.error(f"[FAQGenerator] Failed to generate focused FAQ: {e}")
            return {
                "raw_faqs": [],
                "steps": ["generate_focused_faq (failed)"]
            }

    async def generate_diverse_faq(self, state: FAQGeneratorState) -> Dict[str, Any]:
        """
        Generate FAQ for multi-topic content

        Args:
            state: Current workflow state

        Returns:
            Partial state with raw_faqs
        """
        logger.info("[FAQGenerator] Generating diverse FAQ (multi topic)")

        combined_text = state.get("combined_text", "")
        num_questions = state.get("num_questions", 5)
        detected_topics = state.get("detected_topics", [])
        topics_str = ", ".join(detected_topics)

        if not combined_text:
            logger.warning("[FAQGenerator] No text to generate FAQ from")
            return {
                "raw_faqs": [],
                "steps": ["generate_diverse_faq (no text)"]
            }

        try:
            # Truncate text
            truncated_text = combined_text[:10000]

            # Build prompt
            prompt = MULTI_TOPIC_FAQ_PROMPT.format(
                num_questions=num_questions,
                topics=topics_str,
                text=truncated_text
            )

            messages = [
                {"role": "system", "content": FAQ_GENERATOR_SYSTEM},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm.chat(messages, temperature=0.7, max_tokens=1500)

            # Parse JSON array
            raw_faqs = self._parse_json_array(response)

            logger.info(f"[FAQGenerator] Generated {len(raw_faqs)} diverse FAQs")

            return {
                "raw_faqs": raw_faqs,
                "steps": ["generate_diverse_faq"]
            }

        except Exception as e:
            logger.error(f"[FAQGenerator] Failed to generate diverse FAQ: {e}")
            return {
                "raw_faqs": [],
                "steps": ["generate_diverse_faq (failed)"]
            }

    async def deduplicate(self, state: FAQGeneratorState) -> Dict[str, Any]:
        """
        Remove duplicate FAQs based on question similarity

        Args:
            state: Current workflow state

        Returns:
            Partial state with deduplicated faqs
        """
        logger.info("[FAQGenerator] Deduplicating FAQs")

        raw_faqs = state.get("raw_faqs", [])

        if not raw_faqs:
            return {
                "faqs": [],
                "total_generated": 0,
                "steps": ["deduplicate (no faqs)"]
            }

        # Simple deduplication: remove exact duplicates and very similar questions
        seen_questions = set()
        unique_faqs = []

        for faq in raw_faqs:
            question = faq.get("question", "").strip().lower()

            # Skip if empty
            if not question:
                continue

            # Check for exact duplicates
            if question in seen_questions:
                logger.debug(f"[FAQGenerator] Duplicate removed: {question[:50]}")
                continue

            seen_questions.add(question)
            unique_faqs.append(faq)

        logger.info(f"[FAQGenerator] Deduplicated: {len(raw_faqs)} → {len(unique_faqs)} FAQs")

        return {
            "faqs": unique_faqs,
            "total_generated": len(unique_faqs),
            "steps": ["deduplicate"]
        }

    def _parse_json_object(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON object from LLM response

        Args:
            response: LLM response text

        Returns:
            Parsed dict or empty dict
        """
        try:
            # Try to extract JSON object from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
            else:
                logger.warning("No JSON object found in response")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {}

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
