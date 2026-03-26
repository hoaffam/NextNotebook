"""
Notebooks API Routes
CRUD operations for notebooks with MongoDB persistence
Requires authentication
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone
import uuid
from bson import ObjectId

from ...models.notebook import (
    NotebookCreate,
    NotebookUpdate,
    NotebookResponse,
    NotebookListResponse
)
from ...models.user import UserResponse
from ...database.mongodb_client import get_mongodb, MongoDBClient
from ...database.milvus_client import get_milvus_service, MilvusService
from ...services.summarizer.summarizer_service import get_summarizer_service
from ..routes.auth import get_current_user
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=NotebookListResponse)
async def list_notebooks(
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """Get all notebooks for current user"""
    notebooks_cursor = mongodb.notebooks.find(
        {"user_id": current_user.id}
    ).sort("created_at", -1)
    
    notebooks = []
    for doc in notebooks_cursor:
        notebooks.append(NotebookResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            description=doc.get("description"),
            sources_count=doc.get("sources_count", 0),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"]
        ))
    
    return NotebookListResponse(
        notebooks=notebooks,
        total=len(notebooks)
    )


@router.post("/", response_model=NotebookResponse)
async def create_notebook(
    notebook: NotebookCreate,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """Create a new notebook for current user"""
    now = datetime.now(timezone.utc)
    
    notebook_doc = {
        "user_id": current_user.id,
        "name": notebook.name,
        "description": notebook.description,
        "sources_count": 0,
        "created_at": now,
        "updated_at": now
    }
    
    result = mongodb.notebooks.insert_one(notebook_doc)
    notebook_id = str(result.inserted_id)
    
    logger.info(f"Created notebook: {notebook_id} - {notebook.name} for user: {current_user.id}")
    
    return NotebookResponse(
        id=notebook_id,
        name=notebook.name,
        description=notebook.description,
        sources_count=0,
        created_at=now,
        updated_at=now
    )


@router.get("/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(
    notebook_id: str,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """Get a specific notebook (must belong to current user)"""
    try:
        notebook_doc = mongodb.notebooks.find_one({
            "_id": ObjectId(notebook_id),
            "user_id": current_user.id
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    if not notebook_doc:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    return NotebookResponse(
        id=str(notebook_doc["_id"]),
        name=notebook_doc["name"],
        description=notebook_doc.get("description"),
        sources_count=notebook_doc.get("sources_count", 0),
        created_at=notebook_doc["created_at"],
        updated_at=notebook_doc["updated_at"]
    )


@router.put("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(
    notebook_id: str,
    notebook: NotebookUpdate,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """Update a notebook"""
    try:
        notebook_doc = mongodb.notebooks.find_one({
            "_id": ObjectId(notebook_id),
            "user_id": current_user.id
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    if not notebook_doc:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc)}
    if notebook.name is not None:
        update_data["name"] = notebook.name
    if notebook.description is not None:
        update_data["description"] = notebook.description
    
    mongodb.notebooks.update_one(
        {"_id": ObjectId(notebook_id)},
        {"$set": update_data}
    )
    
    # Fetch updated document
    updated_doc = mongodb.notebooks.find_one({"_id": ObjectId(notebook_id)})
    
    logger.info(f"Updated notebook: {notebook_id}")
    
    return NotebookResponse(
        id=str(updated_doc["_id"]),
        name=updated_doc["name"],
        description=updated_doc.get("description"),
        sources_count=updated_doc.get("sources_count", 0),
        created_at=updated_doc["created_at"],
        updated_at=updated_doc["updated_at"]
    )


@router.delete("/{notebook_id}")
async def delete_notebook(
    notebook_id: str,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb),
    milvus: MilvusService = Depends(get_milvus_service)
):
    """Delete a notebook and all its documents"""
    try:
        notebook_doc = mongodb.notebooks.find_one({
            "_id": ObjectId(notebook_id),
            "user_id": current_user.id
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    if not notebook_doc:
        raise HTTPException(status_code=404, detail="Notebook not found")
    
    # Delete documents from MongoDB
    mongodb.documents.delete_many({"notebook_id": notebook_id})
    
    # Delete vectors from Milvus
    try:
        milvus.delete_by_notebook(notebook_id)
    except Exception as e:
        logger.warning(f"Failed to delete vectors from Milvus: {e}")
    
    # Delete notebook
    mongodb.notebooks.delete_one({"_id": ObjectId(notebook_id)})
    
    logger.info(f"Deleted notebook: {notebook_id}")
    
    return {"message": "Notebook deleted successfully"}


@router.get("/{notebook_id}/overview")
async def get_notebook_overview(
    notebook_id: str,
    force_refresh: bool = False,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """
    Get notebook overview with document summaries (cached)
    
    Args:
        force_refresh: Force regenerate overview (default: False)
    
    Returns:
    - Combined overview of all documents
    - Individual document summaries
    - Suggested questions
    - Main topics across all documents
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
    
    # Get all documents with their summaries
    docs_cursor = mongodb.documents.find({"notebook_id": notebook_id})
    
    documents = []
    for doc in docs_cursor:
        documents.append({
            "id": doc["_id"],
            "filename": doc["filename"],
            "summary": doc.get("summary", ""),
            "key_topics": doc.get("key_topics", []),
            "categories": doc.get("categories", []),
            "chunks_count": doc.get("chunks_count", 0)
        })
    
    # Check if overview is cached and still valid
    cached_overview = notebook_doc.get("cached_overview")
    cached_doc_count = notebook_doc.get("cached_overview_doc_count", 0)

    # Use cache if: exists, is dict (new format), not forced refresh, and doc count matches
    if cached_overview and isinstance(cached_overview, dict) and not force_refresh and cached_doc_count == len(documents):
        logger.info(f"Using cached overview for notebook {notebook_id}")
        return {
            "notebook_id": notebook_id,
            "notebook_name": notebook_doc["name"],
            **cached_overview,
            "documents": documents,
            "cached": True
        }

    # If cached_overview is old string format, ignore it and regenerate
    if cached_overview and isinstance(cached_overview, str):
        logger.info(f"Found old cache format for notebook {notebook_id}, regenerating...")
    
    # Generate new overview if no documents
    if not documents:
        return {
            "notebook_id": notebook_id,
            "notebook_name": notebook_doc["name"],
            "overview": "",
            "main_topics": [],
            "suggested_questions": [],
            "documents": [],
            "total_sources": 0,
            "cached": False
        }
    
    # Generate notebook overview using Summarizer workflow
    logger.info(f"Generating new overview for notebook {notebook_id}")
    summarizer_service = get_summarizer_service()
    result = await summarizer_service.summarize_notebook(notebook_id=notebook_id)

    # Extract fields from result
    overview_data = {
        "overview": result.get("overview", ""),
        "main_topics": result.get("main_topics", []),
        "suggested_questions": result.get("suggested_questions", []),
        "total_sources": result.get("total_sources", 0)
    }

    # Cache the overview in MongoDB
    mongodb.notebooks.update_one(
        {"_id": ObjectId(notebook_id)},
        {"$set": {
            "cached_overview": overview_data,
            "cached_overview_doc_count": len(documents),
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    logger.info(f"Cached overview for notebook {notebook_id}")

    return {
        "notebook_id": notebook_id,
        "notebook_name": notebook_doc["name"],
        **overview_data,
        "documents": documents,
        "cached": False
    }
