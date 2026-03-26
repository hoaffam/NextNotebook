"""
Summarizer Workflow
LangGraph workflow for document and notebook summarization
"""

from langgraph.graph import StateGraph, END
from app.services.summarizer.state import SummarizerState
from app.services.summarizer.nodes import SummarizerNodes
from app.services.summarizer.edges import route_by_style
from app.database.mongodb_client import MongoDBClient
from app.database.milvus_client import MilvusService
from app.services.shared.llm_service import LLMService
from app.services.shared.embedding_service import EmbeddingService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_summarizer_workflow(
    mongodb_client: MongoDBClient,
    milvus_service: MilvusService,
    llm_service: LLMService,
    embedding_service: EmbeddingService
) -> StateGraph:
    """
    Create the Summarizer workflow graph

    Workflow:
    START → retrieve_documents → [route_by_style]
                                     ↓ document → generate_document_summary → END
                                     ↓ notebook → generate_notebook_overview → END

    Args:
        mongodb_client: MongoDB client
        milvus_service: Milvus service
        llm_service: LLM service
        embedding_service: Embedding service

    Returns:
        Compiled StateGraph workflow
    """

    # Initialize nodes
    nodes = SummarizerNodes(
        mongodb_client=mongodb_client,
        milvus_service=milvus_service,
        llm_service=llm_service,
        embedding_service=embedding_service
    )

    # Create the graph
    workflow = StateGraph(SummarizerState)

    # Add nodes
    workflow.add_node("retrieve_documents", nodes.retrieve_documents)
    workflow.add_node("generate_document_summary", nodes.generate_document_summary)
    workflow.add_node("generate_notebook_overview", nodes.generate_notebook_overview)

    # Set entry point
    workflow.set_entry_point("retrieve_documents")

    # Add conditional edge based on style
    workflow.add_conditional_edges(
        "retrieve_documents",
        route_by_style,
        {
            "document": "generate_document_summary",
            "notebook": "generate_notebook_overview"
        }
    )

    # Both paths lead to END
    workflow.add_edge("generate_document_summary", END)
    workflow.add_edge("generate_notebook_overview", END)

    # Compile the graph
    compiled = workflow.compile()

    logger.info("Summarizer workflow created successfully")

    return compiled
