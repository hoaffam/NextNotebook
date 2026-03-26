"""
Admin API Routes
Database management operations
"""

from fastapi import APIRouter, Depends, HTTPException
from ...database.milvus_client import get_milvus_service, MilvusService
from ...database.mongodb_client import get_mongodb, MongoDBClient
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/reset-vectors")
async def reset_vector_database(
    milvus: MilvusService = Depends(get_milvus_service)
):
    """
    Reset the vector database (drop and recreate collection)
    WARNING: This will delete all vector data!
    """
    success = milvus.reset_collection()
    
    if success:
        logger.info("Vector database reset successfully")
        return {"message": "Vector database reset successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reset vector database")


@router.get("/stats")
async def get_database_stats(
    mongodb: MongoDBClient = Depends(get_mongodb),
    milvus: MilvusService = Depends(get_milvus_service)
):
    """Get database statistics"""
    try:
        # MongoDB stats
        users_count = mongodb.users.count_documents({})
        notebooks_count = mongodb.notebooks.count_documents({})
        documents_count = mongodb.documents.count_documents({})
        
        # Milvus stats
        all_vectors = await milvus.list_all_documents()
        vectors_count = len(all_vectors)
        
        return {
            "mongodb": {
                "users": users_count,
                "notebooks": notebooks_count,
                "documents": documents_count
            },
            "milvus": {
                "vectors": vectors_count
            }
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
