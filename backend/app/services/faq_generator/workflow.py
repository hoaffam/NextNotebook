"""
FAQ Generator Workflow
LangGraph workflow for FAQ generation
"""

from langgraph.graph import StateGraph, END
from app.services.faq_generator.state import FAQGeneratorState
from app.services.faq_generator.nodes import FAQGeneratorNodes
from app.services.faq_generator.edges import route_by_topic_type
from app.database.milvus_client import MilvusService
from app.services.shared.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_faq_workflow(
    milvus_service: MilvusService,
    llm_service: LLMService
) -> StateGraph:
    """
    Create the FAQ Generator workflow graph

    Workflow:
    START → retrieve_chunks → topic_extraction → [route_by_topic_type]
                                                     ↓ single → generate_focused_faq → deduplicate → END
                                                     ↓ multi → generate_diverse_faq → deduplicate → END

    Args:
        milvus_service: Milvus service
        llm_service: LLM service

    Returns:
        Compiled StateGraph workflow
    """

    # Initialize nodes
    nodes = FAQGeneratorNodes(
        milvus_service=milvus_service,
        llm_service=llm_service
    )

    # Create the graph
    workflow = StateGraph(FAQGeneratorState)

    # Add nodes
    workflow.add_node("retrieve_chunks", nodes.retrieve_chunks)
    workflow.add_node("topic_extraction", nodes.topic_extraction)
    workflow.add_node("generate_focused_faq", nodes.generate_focused_faq)
    workflow.add_node("generate_diverse_faq", nodes.generate_diverse_faq)
    workflow.add_node("deduplicate", nodes.deduplicate)

    # Set entry point
    workflow.set_entry_point("retrieve_chunks")

    # Add edges
    workflow.add_edge("retrieve_chunks", "topic_extraction")

    # Conditional routing based on topic type
    workflow.add_conditional_edges(
        "topic_extraction",
        route_by_topic_type,
        {
            "single": "generate_focused_faq",
            "multi": "generate_diverse_faq"
        }
    )

    # Both paths converge at deduplicate
    workflow.add_edge("generate_focused_faq", "deduplicate")
    workflow.add_edge("generate_diverse_faq", "deduplicate")

    # Deduplicate leads to END
    workflow.add_edge("deduplicate", END)

    # Compile the graph
    compiled = workflow.compile()

    logger.info("FAQ Generator workflow created successfully")

    return compiled
