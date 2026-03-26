"""
Summarizer Workflow Nodes
Node functions for the Summarizer LangGraph workflow
"""

import json
from typing import Dict, Any
from bson import ObjectId
from app.services.summarizer.state import SummarizerState
from app.services.summarizer.strategies import (
    DOCUMENT_SUMMARY_PROMPT,
    NOTEBOOK_OVERVIEW_PROMPT,
    DOCUMENT_ANALYZER_SYSTEM,
    RESEARCH_ASSISTANT_SYSTEM
)
from app.database.mongodb_client import MongoDBClient
from app.database.milvus_client import MilvusService
from app.services.shared.llm_service import LLMService
from app.services.shared.embedding_service import EmbeddingService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SummarizerNodes:
    """Node functions for Summarizer workflow"""

    def __init__(
        self,
        mongodb_client: MongoDBClient,
        milvus_service: MilvusService,
        llm_service: LLMService,
        embedding_service: EmbeddingService
    ):
        """
        Initialize nodes with dependencies

        Args:
            mongodb_client: MongoDB client for documents
            milvus_service: Milvus service for vector search
            llm_service: LLM service for generation
            embedding_service: Embedding service
        """
        self.mongodb = mongodb_client
        self.milvus = milvus_service
        self.llm = llm_service
        self.embedding = embedding_service

    async def retrieve_documents(self, state: SummarizerState) -> Dict[str, Any]:
        """
        Retrieve documents from MongoDB

        Args:
            state: Current workflow state

        Returns:
            Partial state with documents
        """
        logger.info(f"[Summarizer] Retrieving documents for notebook_id={state['notebook_id']}")

        documents = []

        try:
            if state.get("document_id"):
                # Single document
                doc = self.mongodb.documents.find_one({"_id": ObjectId(state["document_id"])})
                if doc:
                    documents = [doc]
            else:
                # All documents in notebook - query by notebook_id field
                documents = list(self.mongodb.documents.find({"notebook_id": state["notebook_id"]}))

            logger.info(f"[Summarizer] Retrieved {len(documents)} documents")

            return {
                "documents": documents,
                "document_count": len(documents),
                "steps": ["retrieve_documents"]
            }

        except Exception as e:
            logger.error(f"[Summarizer] Failed to retrieve documents: {e}")
            return {
                "documents": [],
                "document_count": 0,
                "steps": ["retrieve_documents (failed)"]
            }

    async def generate_document_summary(self, state: SummarizerState) -> Dict[str, Any]:
        """
        Generate summary for a single document

        Args:
            state: Current workflow state

        Returns:
            Partial state with summary and key_topics
        """
        logger.info("[Summarizer] Generating document summary")

        if not state["documents"]:
            return {
                "summary": "No document found.",
                "key_topics": [],
                "sources_used": 0,
                "steps": ["generate_document_summary (no docs)"]
            }

        try:
            doc = state["documents"][0]  # Single document
            filename = doc.get("filename", "Unknown")
            text = doc.get("text", "")[:15000]  # Truncate to 15k chars

            # Build prompt
            prompt = DOCUMENT_SUMMARY_PROMPT.format(
                filename=filename,
                text=text
            )

            messages = [
                {"role": "system", "content": DOCUMENT_ANALYZER_SYSTEM},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm.chat(messages, temperature=0.3, max_tokens=1000)

            # Parse JSON response
            result = self._parse_json_response(response, fallback_summary=text[:500])

            summary = result.get("summary", "")[:state.get("max_length", 500)]
            key_topics = result.get("key_topics", [])

            # Generate embedding for summary
            summary_embedding = await self.embedding.embed_text(summary)

            logger.info(f"[Summarizer] Generated summary: {len(summary)} chars, {len(key_topics)} topics")

            return {
                "summary": summary,
                "key_topics": key_topics,
                "summary_embedding": summary_embedding,
                "sources_used": 1,
                "steps": ["generate_document_summary"]
            }

        except Exception as e:
            logger.error(f"[Summarizer] Failed to generate document summary: {e}")
            return {
                "summary": f"Failed to generate summary: {str(e)}",
                "key_topics": [],
                "summary_embedding": None,
                "sources_used": 0,
                "steps": ["generate_document_summary (failed)"]
            }

    async def generate_notebook_overview(self, state: SummarizerState) -> Dict[str, Any]:
        """
        Generate overview for entire notebook

        Args:
            state: Current workflow state

        Returns:
            Partial state with overview, suggested_questions, key_topics
        """
        logger.info("[Summarizer] Generating notebook overview")

        documents = state.get("documents", [])

        if not documents:
            return {
                "summary": "Notebook này chưa có tài liệu nào. Hãy upload tài liệu để bắt đầu!",
                "suggested_questions": [],
                "key_topics": [],
                "sources_used": 0,
                "steps": ["generate_notebook_overview (no docs)"]
            }

        try:
            # Combine all document summaries
            summaries_text = "\n\n".join([
                f"📄 {doc.get('filename', 'Unknown')}:\n{doc.get('summary', 'No summary')}"
                for doc in documents
            ])

            # Collect all key topics
            all_topics = []
            for doc in documents:
                all_topics.extend(doc.get("key_topics", []))

            # Get unique topics (max 10)
            unique_topics = list(set(all_topics))[:10]

            # Get notebook name
            notebook = self.mongodb.notebooks.find_one({"_id": ObjectId(state["notebook_id"])})
            notebook_name = notebook.get("name", "Unnamed Notebook") if notebook else "Unnamed Notebook"

            # Build prompt
            prompt = NOTEBOOK_OVERVIEW_PROMPT.format(
                notebook_name=notebook_name,
                summaries_text=summaries_text
            )

            messages = [
                {"role": "system", "content": RESEARCH_ASSISTANT_SYSTEM},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm.chat(messages, temperature=0.3, max_tokens=800)

            # Parse JSON response
            result = self._parse_json_response(
                response,
                fallback_summary=f"Notebook chứa {len(documents)} tài liệu."
            )

            overview = result.get("overview", "")
            suggested_questions = result.get("suggested_questions", [])

            logger.info(f"[Summarizer] Generated overview: {len(overview)} chars, {len(suggested_questions)} questions")

            return {
                "summary": overview,
                "suggested_questions": suggested_questions,
                "key_topics": unique_topics,
                "sources_used": len(documents),
                "steps": ["generate_notebook_overview"]
            }

        except Exception as e:
            logger.error(f"[Summarizer] Failed to generate notebook overview: {e}")
            return {
                "summary": f"Notebook chứa {len(documents)} tài liệu.",
                "suggested_questions": [],
                "key_topics": [],
                "sources_used": len(documents),
                "steps": ["generate_notebook_overview (failed)"]
            }

    def _parse_json_response(self, response: str, fallback_summary: str = "") -> Dict[str, Any]:
        """
        Parse JSON from LLM response

        Args:
            response: LLM response text
            fallback_summary: Fallback summary if parsing fails

        Returns:
            Parsed dict or fallback dict
        """
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(response[json_start:json_end])
            else:
                raise ValueError("No JSON found")
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse JSON summary, using fallback")
            return {
                "summary": fallback_summary or response,
                "key_topics": [],
                "suggested_questions": []
            }
