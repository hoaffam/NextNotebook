"""
Summary API Routes
Document summarization using Summarizer module
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.models.summary import SummaryRequest, SummaryResponse
from app.api.deps import get_summarizer_service
from app.services.summarizer.summarizer_service import SummarizerService
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/", response_model=SummaryResponse)
async def summarize(
    request: SummaryRequest,
    summarizer_service: SummarizerService = Depends(get_summarizer_service)
):
    """
    Summarize documents in a notebook using Summarizer workflow

    Args:
        notebook_id: ID of the notebook to summarize
        style: Summary style (not used in new implementation)
        max_length: Maximum length of summary
    """
    try:
        # Use Summarizer workflow for notebook overview
        result = await summarizer_service.summarize_notebook(
            notebook_id=request.notebook_id
        )

        if not result.get("overview"):
            raise HTTPException(
                status_code=404,
                detail="No documents found in notebook"
            )

        return SummaryResponse(
            summary=result.get("overview", ""),
            sources_used=result.get("total_sources", 0),
            style=request.style
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document/{document_id}", response_model=SummaryResponse)
async def summarize_document(
    document_id: str,
    style: Optional[str] = "document",
    max_length: Optional[int] = 500,
    summarizer_service: SummarizerService = Depends(get_summarizer_service)
):
    """Summarize a specific document using Summarizer workflow"""
    try:
        # Use Summarizer workflow for document summary
        result = await summarizer_service.summarize_document(
            document_id=document_id,
            max_length=max_length
        )

        if not result.get("summary"):
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        return SummaryResponse(
            summary=result.get("summary", ""),
            sources_used=1,
            style=style
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
