"""
MCQ Generator Workflow
LangGraph workflow for multiple-choice question generation
"""

from langgraph.graph import StateGraph, END
from app.services.mcq_generator.state import MCQGeneratorState
from app.services.mcq_generator.nodes import MCQGeneratorNodes
from app.services.mcq_generator.edges import check_chunk_availability
from app.database.milvus_client import MilvusService
from app.services.shared.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_mcq_workflow(
    milvus_service: MilvusService,
    llm_service: LLMService
) -> StateGraph:
    """
    Create the MCQ Generator workflow graph

    Workflow:
    START → retrieve_chunks → diversity_sampling → batch_generate →
            validate_questions → format_output → END

    Args:
        milvus_service: Milvus service
        llm_service: LLM service

    Returns:
        Compiled StateGraph workflow
    """

    # Initialize nodes
    nodes = MCQGeneratorNodes(
        milvus_service=milvus_service,
        llm_service=llm_service
    )

    # Create the graph
    workflow = StateGraph(MCQGeneratorState)

    # Add nodes
    workflow.add_node("retrieve_chunks", nodes.retrieve_chunks)
    workflow.add_node("diversity_sampling", nodes.diversity_sampling)
    workflow.add_node("batch_generate", nodes.batch_generate)
    workflow.add_node("validate_questions", nodes.validate_questions)
    workflow.add_node("format_output", nodes.format_output)

    # Set entry point
    workflow.set_entry_point("retrieve_chunks")

    # Add edges (linear flow for MCQ generation)
    workflow.add_edge("retrieve_chunks", "diversity_sampling")
    workflow.add_edge("diversity_sampling", "batch_generate")
    workflow.add_edge("batch_generate", "validate_questions")
    workflow.add_edge("validate_questions", "format_output")
    workflow.add_edge("format_output", END)

    # Compile the graph
    compiled = workflow.compile()

    logger.info("MCQ Generator workflow created successfully")

    return compiled
