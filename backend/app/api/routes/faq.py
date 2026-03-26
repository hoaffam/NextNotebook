"""
FAQ API Routes
Generate FAQs from documents
"""

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from app.models.faq import FAQGenerateRequest, FAQResponse, FAQItem
from app.models.user import UserResponse
from app.api.deps import get_faq_service
from app.services.faq_generator.faq_service import FAQGeneratorService
from app.database.mongodb_client import get_mongodb, MongoDBClient
from ..routes.auth import get_current_user
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/generate", response_model=FAQResponse)
async def generate_faq(
    request: FAQGenerateRequest,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb),
    faq_service: FAQGeneratorService = Depends(get_faq_service)
):
    """
    Generate FAQ from notebook documents using FAQ Generator workflow
    """
    try:
        # Verify notebook belongs to user
        notebook_doc = mongodb.notebooks.find_one({
            "_id": ObjectId(request.notebook_id),
            "user_id": current_user.id
        })
        if not notebook_doc:
            raise HTTPException(status_code=404, detail="Notebook not found")

        # Generate FAQ using FAQ Generator workflow
        faqs = await faq_service.generate_faq(
            notebook_id=request.notebook_id,
            num_questions=request.num_questions
        )

        if not faqs:
            raise HTTPException(
                status_code=400,
                detail="Could not generate FAQ. Make sure the notebook has documents."
            )

        # Extract unique topics
        topics = list(set([faq.get("topic", "") for faq in faqs if faq.get("topic")]))

        # Convert to FAQItem format
        faq_items = [
            FAQItem(
                question=faq.get("question", ""),
                answer=faq.get("answer", ""),
                topic=faq.get("topic")
            )
            for faq in faqs
        ]

        logger.info(f"Generated {len(faq_items)} FAQs for notebook {request.notebook_id}")

        return FAQResponse(
            faqs=faq_items,
            total=len(faq_items),
            topics=topics
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FAQ generation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
