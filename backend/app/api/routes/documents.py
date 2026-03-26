"""
Documents API Routes
Upload and manage documents with MongoDB + Milvus
Requires authentication
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import os
import aiofiles
from bson import ObjectId

from ...config import get_settings
from ...models.document import DocumentResponse, DocumentListResponse, CategoryAssignment
from ...models.user import UserResponse
from ...core.document_processor import DocumentProcessor
from ...core.text_chunker import TextChunker
from ...database.milvus_client import MilvusService
from ...database.mongodb_client import get_mongodb, MongoDBClient
from ...api.deps import (
    get_milvus_service,
    get_embedding_service,
    get_summarizer_service,
    get_classification_service
)
from ...services.shared.embedding_service import EmbeddingService
from ..routes.auth import get_current_user
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    notebook_id: str = Form(...),
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb),
    milvus: MilvusService = Depends(get_milvus_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """
    Upload a document (PDF, DOCX, TXT) and process it
    
    1. Verify notebook belongs to user
    2. Save file to disk
    3. Extract text
    4. Chunk text
    5. Generate embeddings
    6. Store metadata in MongoDB
    7. Store vectors in Milvus
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
    
    # Validate file extension
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Generate document ID
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}.{file_ext}")
    
    try:
        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        logger.info(f"Saved file: {file_path}")

        # Extract structured data with metadata
        processor = DocumentProcessor()
        structured_data = processor.extract_structured(file_path)

        file_type = structured_data["file_type"]
        plain_text = structured_data["plain_text"]

        if not plain_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from document")

        logger.info(f"Extracted {len(plain_text)} characters from {file_type.upper()} document")

        # Smart chunking based on file type
        chunker = TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

        if file_type == "pdf":
            chunks = chunker.chunk_pdf(structured_data["data"])
        elif file_type == "docx":
            chunks = chunker.chunk_docx(structured_data["data"])
        elif file_type == "txt":
            chunks = chunker.chunk_txt(structured_data["data"], line_tracking=True)
        else:
            # Fallback to regular chunking
            chunks = chunker.chunk_text(plain_text)

        logger.info(f"Created {len(chunks)} chunks using {file_type.upper()}-specific strategy")
        
        # Generate embeddings
        embeddings = await embedding_service.embed_texts([c["text"] for c in chunks])
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Generate document summary and key topics
        summarizer_service = get_summarizer_service()
        summary_result = await summarizer_service.generate_document_summary(
            text=plain_text,
            filename=file.filename
        )

        logger.info(f"Generated summary: {len(summary_result.get('summary', ''))} chars")

        # Classify document
        classification_service = get_classification_service()
        categories = []
        if summary_result.get("summary_embedding"):
            categories = await classification_service.classify_document(
                summary_embedding=summary_result["summary_embedding"],
                summary_text=summary_result.get("summary", ""),
                key_topics=summary_result.get("key_topics", [])
            )
        
        logger.info(f"Classified document: {[c['category'] for c in categories]}")
        
        # Store metadata in MongoDB
        now = datetime.now(timezone.utc)
        document_doc = {
            "_id": doc_id,
            "notebook_id": notebook_id,
            "user_id": current_user.id,
            "filename": file.filename,
            "file_path": file_path,
            "file_size": len(content),
            "chunks_count": len(chunks),
            "status": "processed",
            # New fields
            "summary": summary_result.get("summary", ""),
            "key_topics": summary_result.get("key_topics", []),
            "summary_embedding": summary_result.get("summary_embedding"),
            "categories": categories,
            "created_at": now,
            "updated_at": now
        }
        mongodb.documents.insert_one(document_doc)
        
        # Update notebook sources count and invalidate overview cache
        mongodb.notebooks.update_one(
            {"_id": ObjectId(notebook_id)},
            {
                "$inc": {"sources_count": 1},
                "$set": {"updated_at": now},
                "$unset": {"cached_overview": "", "cached_overview_doc_count": ""}
            }
        )
        
        # Store vectors in Milvus
        await milvus.insert_documents(
            doc_id=doc_id,
            notebook_id=notebook_id,
            filename=file.filename,
            chunks=chunks,
            embeddings=embeddings
        )
        
        logger.info(f"Stored document in Milvus: {doc_id}")
        
        # Build category assignments for response
        category_assignments = [
            CategoryAssignment(
                category=c["category"],
                score=c["score"],
                confidence=c["confidence"],
                is_auto=c["is_auto"],
                suggested=c.get("suggested")
            )
            for c in categories
        ]
        
        return DocumentResponse(
            id=doc_id,
            filename=file.filename,
            notebook_id=notebook_id,
            chunks_count=len(chunks),
            status="processed",
            summary=summary_result.get("summary", ""),
            key_topics=summary_result.get("key_topics", []),
            categories=category_assignments,
            created_at=now
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        # Cleanup on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notebook/{notebook_id}", response_model=DocumentListResponse)
async def list_documents(
    notebook_id: str,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """Get all documents in a notebook"""
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
    
    # Get documents from MongoDB
    docs_cursor = mongodb.documents.find({"notebook_id": notebook_id})
    
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


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user),
    mongodb: MongoDBClient = Depends(get_mongodb),
    milvus: MilvusService = Depends(get_milvus_service)
):
    """Delete a document"""
    # Find document
    doc = mongodb.documents.find_one({
        "_id": document_id,
        "user_id": current_user.id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    notebook_id = doc["notebook_id"]
    
    # Delete from Milvus
    try:
        await milvus.delete_document(document_id)
    except Exception as e:
        logger.warning(f"Failed to delete from Milvus: {e}")
    
    # Delete file from disk
    file_path = doc.get("file_path")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from MongoDB
    mongodb.documents.delete_one({"_id": document_id})
    
    # Update notebook sources count and invalidate overview cache
    mongodb.notebooks.update_one(
        {"_id": ObjectId(notebook_id)},
        {
            "$inc": {"sources_count": -1},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$unset": {"cached_overview": "", "cached_overview_doc_count": ""}
        }
    )
    
    logger.info(f"Deleted document: {document_id}")
    
    return {"message": "Document deleted successfully"}
