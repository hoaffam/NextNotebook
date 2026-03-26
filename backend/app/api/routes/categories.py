"""
Categories API Routes
Manage document categories
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from bson import ObjectId

from ...models.category import (
    CategoryListResponse,
    CategoryInfo,
    UpdateCategoryRequest,
    CategoryFilterRequest
)
from ...models.document import DocumentResponse, DocumentListResponse, CategoryAssignment
from ...models.user import UserResponse
from ...services.shared.classification_service import get_classification_service
from ...database.mongodb_client import get_mongodb, MongoDBClient
from ..routes.auth import get_current_user
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=CategoryListResponse)
async def list_categories():
    """Get all available categories for classification"""
    classification_service = get_classification_service()
    categories = classification_service.get_all_categories()
    
    return CategoryListResponse(
        categories=[CategoryInfo(**cat) for cat in categories],
        total=len(categories)
    )


@router.put("/document")
async def update_document_categories(
    request: UpdateCategoryRequest,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """
    Update categories for a document (user override)
    
    This allows users to manually assign categories to a document,
    overriding the AI classification.
    """
    # Verify document belongs to user
    doc = mongodb.documents.find_one({
        "_id": request.document_id,
        "user_id": current_user.id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update categories
    classification_service = get_classification_service()
    success = await classification_service.update_document_category(
        document_id=request.document_id,
        categories=request.categories,
        mongodb_client=mongodb
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update categories")
    
    logger.info(f"Updated categories for document {request.document_id}: {request.categories}")
    
    return {"message": "Categories updated successfully", "categories": request.categories}


@router.post("/filter", response_model=DocumentListResponse)
async def filter_documents_by_category(
    request: CategoryFilterRequest,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """
    Filter documents in a notebook by categories
    
    Returns documents that match any of the specified categories.
    If categories list is empty, returns all documents.
    """
    # Verify notebook belongs to user
    try:
        notebook_doc = mongodb.notebooks.find_one({
            "_id": ObjectId(request.notebook_id),
            "user_id": current_user.id
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    if not notebook_doc:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    # Build query
    query = {"notebook_id": request.notebook_id}
    
    if request.categories:
        # Filter by specific categories
        category_conditions = [
            {"categories.category": {"$in": request.categories}}
        ]
        
        if request.include_uncategorized:
            category_conditions.append({"categories": {"$size": 0}})
            category_conditions.append({"categories.category": "Uncategorized"})
        
        query["$or"] = category_conditions
    
    # Get documents
    docs_cursor = mongodb.documents.find(query)
    
    documents = []
    for doc in docs_cursor:
        # Build category assignments
        categories = []
        for c in doc.get("categories", []):
            categories.append(CategoryAssignment(
                category=c.get("category", "Uncategorized"),
                score=c.get("score", 0),
                confidence=c.get("confidence", "low"),
                is_auto=c.get("is_auto", True),
                suggested=c.get("suggested")
            ))
        
        documents.append(DocumentResponse(
            id=doc["_id"],
            filename=doc["filename"],
            notebook_id=doc["notebook_id"],
            chunks_count=doc.get("chunks_count", 0),
            status=doc.get("status", "unknown"),
            summary=doc.get("summary"),
            key_topics=doc.get("key_topics", []),
            categories=categories,
            created_at=doc.get("created_at")
        ))
    
    return DocumentListResponse(
        documents=documents,
        total=len(documents)
    )


@router.get("/notebook/{notebook_id}/stats")
async def get_category_stats(
    notebook_id: str,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """
    Get category statistics for a notebook
    
    Returns count of documents per category.
    """
    # Verify notebook belongs to user
    try:
        notebook_doc = mongodb.notebooks.find_one({
            "_id": ObjectId(notebook_id),
            "user_id": current_user.id
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    if not notebook_doc:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    # Aggregate category counts
    pipeline = [
        {"$match": {"notebook_id": notebook_id}},
        {"$unwind": {"path": "$categories", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": {"$ifNull": ["$categories.category", "Uncategorized"]},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    results = list(mongodb.documents.aggregate(pipeline))
    
    stats = {
        "total_documents": sum(r["count"] for r in results),
        "categories": [
            {"category": r["_id"], "count": r["count"]}
            for r in results
        ]
    }
    
    return stats
