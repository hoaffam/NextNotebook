"""
Milvus Client
Connect to Zilliz Cloud and manage vector operations
"""

from typing import List, Dict, Optional
from pymilvus import MilvusClient, DataType
import uuid

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class MilvusService:
    """
    Milvus/Zilliz Cloud service for vector storage and search
    """
    
    def __init__(self):
        """Initialize connection to Zilliz Cloud"""
        self.client = None
        self.collection_name = settings.ZILLIZ_COLLECTION_NAME
        self._connect()
    
    def _connect(self):
        """Establish connection to Zilliz Cloud"""
        try:
            if settings.ZILLIZ_CLOUD_URI and settings.ZILLIZ_CLOUD_TOKEN:
                self.client = MilvusClient(
                    uri=settings.ZILLIZ_CLOUD_URI,
                    token=settings.ZILLIZ_CLOUD_TOKEN
                )
                logger.info("Connected to Zilliz Cloud")
                self._ensure_collection()
            else:
                logger.warning("Zilliz Cloud credentials not configured")
                self.client = None
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            self.client = None
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        if self.client is None:
            return
        
        try:
            # Check if collection exists
            if self.client.has_collection(self.collection_name):
                logger.info(f"Collection '{self.collection_name}' already exists")
                return
            
            # Create collection with proper schema for filtering
            from pymilvus import CollectionSchema, FieldSchema
            
            schema = self.client.create_schema(
                auto_id=False,
                enable_dynamic_field=True
            )
            
            # Add fields (base fields - required)
            schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=128)
            schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION)
            schema.add_field(field_name="document_id", datatype=DataType.VARCHAR, max_length=128)
            schema.add_field(field_name="notebook_id", datatype=DataType.VARCHAR, max_length=128)
            schema.add_field(field_name="filename", datatype=DataType.VARCHAR, max_length=512)
            schema.add_field(field_name="chunk_index", datatype=DataType.INT64)
            schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=8000)
            schema.add_field(field_name="word_count", datatype=DataType.INT64)
            schema.add_field(field_name="file_type", datatype=DataType.VARCHAR, max_length=10)  # pdf, docx, txt

            # NOTE: All other citation metadata fields will be stored as dynamic fields
            # Milvus doesn't support nullable fields, so we use enable_dynamic_field=True
            # Dynamic fields: page_number, paragraph_start, paragraph_end (PDF)
            # heading, heading_level, section_path, is_table, table_name (DOCX)
            # line_start, line_end (TXT)
            # char_start, char_end (common)
            
            # Create index params
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="AUTOINDEX",
                metric_type="COSINE"
            )
            # Add index for notebook_id for faster filtering
            index_params.add_index(
                field_name="notebook_id",
                index_type="AUTOINDEX"
            )
            
            # Create collection
            self.client.create_collection(
                collection_name=self.collection_name,
                schema=schema,
                index_params=index_params
            )
            
            logger.info(f"Created collection '{self.collection_name}' with proper schema")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
    
    async def insert_documents(
        self,
        doc_id: str,
        notebook_id: str,
        filename: str,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Insert document chunks with embeddings into Milvus
        
        Args:
            doc_id: Document ID
            notebook_id: Parent notebook ID
            filename: Original filename
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors
        """
        if self.client is None:
            logger.error("Milvus client not connected")
            return False
        
        try:
            data = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{doc_id}_{i}"

                # Base fields (always present)
                chunk_data = {
                    "id": chunk_id,
                    "vector": embedding,
                    "document_id": doc_id,
                    "notebook_id": notebook_id,
                    "filename": filename,
                    "chunk_index": i,
                    "text": chunk["text"][:8000],  # Increased to 8000 for full chunks
                    "word_count": chunk.get("word_count", 0),
                    "file_type": chunk.get("file_type", "txt")
                }

                # Add file-type-specific metadata
                file_type = chunk.get("file_type", "txt")

                if file_type == "pdf":
                    chunk_data.update({
                        "page_number": chunk.get("page_number"),
                        "paragraph_start": chunk.get("paragraph_start"),
                        "paragraph_end": chunk.get("paragraph_end"),
                        "char_start": chunk.get("char_start"),
                        "char_end": chunk.get("char_end")
                    })
                elif file_type == "docx":
                    chunk_data.update({
                        "heading": chunk.get("heading", "")[:500] if chunk.get("heading") else None,
                        "heading_level": chunk.get("heading_level"),
                        "section_path": chunk.get("section_path", "")[:1000] if chunk.get("section_path") else None,
                        "is_table": chunk.get("is_table", False),
                        "table_name": chunk.get("table_name", "")[:200] if chunk.get("table_name") else None,
                        "paragraph_start": chunk.get("paragraph_start"),
                        "paragraph_end": chunk.get("paragraph_end"),
                        "char_start": chunk.get("char_start"),
                        "char_end": chunk.get("char_end")
                    })
                elif file_type == "txt":
                    chunk_data.update({
                        "line_start": chunk.get("line_start"),
                        "line_end": chunk.get("line_end"),
                        "paragraph_start": chunk.get("paragraph_start"),
                        "paragraph_end": chunk.get("paragraph_end")
                    })

                data.append(chunk_data)
            
            self.client.insert(
                collection_name=self.collection_name,
                data=data
            )
            
            logger.info(f"Inserted {len(data)} chunks for document {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert documents: {e}")
            return False
    
    async def search(
        self,
        query_embedding: List[float],
        notebook_id: str,
        top_k: int = None,
        threshold: float = None
    ) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query vector
            notebook_id: Filter by notebook
            top_k: Number of results
            threshold: Minimum similarity threshold
        """
        if self.client is None:
            logger.error("Milvus client not connected")
            return []
        
        top_k = top_k or settings.TOP_K_RESULTS
        threshold = threshold or settings.SIMILARITY_THRESHOLD
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                limit=top_k,
                filter=f'notebook_id == "{notebook_id}"',
                output_fields=["*"]  # Get all fields including dynamic fields
            )
            
            # Process results - NO threshold filter, return all results
            # COSINE distance varies; let the LLM grade relevance instead
            processed = []
            for hits in results:
                for hit in hits:
                    entity = hit["entity"]

                    # Base fields
                    chunk_result = {
                        "id": hit["id"],
                        "document_id": entity["document_id"],
                        "filename": entity["filename"],
                        "chunk_index": entity["chunk_index"],
                        "text": entity["text"],
                        "score": hit["distance"],
                        "file_type": entity.get("file_type", "txt")
                    }

                    # Add file-type-specific metadata
                    file_type = entity.get("file_type", "txt")

                    if file_type == "pdf":
                        chunk_result.update({
                            "page_number": entity.get("page_number"),
                            "paragraph_start": entity.get("paragraph_start"),
                            "paragraph_end": entity.get("paragraph_end"),
                            "char_start": entity.get("char_start"),
                            "char_end": entity.get("char_end")
                        })
                    elif file_type == "docx":
                        chunk_result.update({
                            "heading": entity.get("heading"),
                            "heading_level": entity.get("heading_level"),
                            "section_path": entity.get("section_path"),
                            "is_table": entity.get("is_table", False),
                            "table_name": entity.get("table_name"),
                            "paragraph_start": entity.get("paragraph_start"),
                            "paragraph_end": entity.get("paragraph_end"),
                            "char_start": entity.get("char_start"),
                            "char_end": entity.get("char_end")
                        })
                    elif file_type == "txt":
                        chunk_result.update({
                            "line_start": entity.get("line_start"),
                            "line_end": entity.get("line_end"),
                            "paragraph_start": entity.get("paragraph_start"),
                            "paragraph_end": entity.get("paragraph_end")
                        })

                    processed.append(chunk_result)
            
            logger.info(f"Retrieved {len(processed)} documents")
            return processed
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def get_documents_by_notebook(self, notebook_id: str) -> List[Dict]:
        """Get all documents in a notebook"""
        if self.client is None:
            return []
        
        try:
            # Query for all chunks in notebook
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'notebook_id == "{notebook_id}"',
                output_fields=["document_id", "filename", "chunk_index"],
                limit=1000
            )
            
            # Group by document and count chunks
            doc_chunks = {}
            for r in results:
                doc_id = r["document_id"]
                if doc_id not in doc_chunks:
                    doc_chunks[doc_id] = {
                        "id": doc_id,
                        "filename": r["filename"],
                        "notebook_id": notebook_id,
                        "chunks_count": 0,
                        "status": "processed"
                    }
                doc_chunks[doc_id]["chunks_count"] += 1
            
            return list(doc_chunks.values())
            
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return []
    
    async def get_all_chunks(self, notebook_id: str) -> List[Dict]:
        """Get all chunks for a notebook"""
        if self.client is None:
            return []
        
        try:
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'notebook_id == "{notebook_id}"',
                output_fields=["text", "document_id", "filename", "chunk_index"],
                limit=1000
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get chunks: {e}")
            return []
    
    async def get_chunks_by_document(self, document_id: str) -> List[Dict]:
        """Get all chunks for a specific document"""
        if self.client is None:
            return []
        
        try:
            results = self.client.query(
                collection_name=self.collection_name,
                filter=f'document_id == "{document_id}"',
                output_fields=["text", "chunk_index", "filename"],
                limit=500
            )
            
            # Sort by chunk index
            return sorted(results, key=lambda x: x.get("chunk_index", 0))
            
        except Exception as e:
            logger.error(f"Failed to get document chunks: {e}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks of a document"""
        if self.client is None:
            return False
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                filter=f'document_id == "{document_id}"'
            )
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    async def delete_notebook_documents(self, notebook_id: str) -> bool:
        """Delete all documents in a notebook"""
        if self.client is None:
            return False
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                filter=f'notebook_id == "{notebook_id}"'
            )
            logger.info(f"Deleted all documents in notebook {notebook_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete notebook documents: {e}")
            return False
    
    def delete_by_notebook(self, notebook_id: str) -> bool:
        """Sync method to delete all documents in a notebook"""
        if self.client is None:
            return False
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                filter=f'notebook_id == "{notebook_id}"'
            )
            logger.info(f"Deleted all vectors for notebook {notebook_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete notebook vectors: {e}")
            return False
    
    def reset_collection(self) -> bool:
        """Drop and recreate the collection (reset all data)"""
        if self.client is None:
            return False
        
        try:
            if self.client.has_collection(self.collection_name):
                self.client.drop_collection(self.collection_name)
                logger.info(f"Dropped collection '{self.collection_name}'")
            
            self._ensure_collection()
            logger.info(f"Reset collection '{self.collection_name}' complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False
    
    async def list_all_documents(self) -> List[Dict]:
        """List all documents in the collection (for debugging)"""
        if self.client is None:
            return []
        
        try:
            results = self.client.query(
                collection_name=self.collection_name,
                filter="",
                output_fields=["document_id", "notebook_id", "filename", "chunk_index"],
                limit=100
            )
            logger.info(f"Found {len(results)} total chunks in collection")
            return results
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []


# Global instance
_milvus_service: MilvusService = None


def get_milvus_service() -> MilvusService:
    """Get Milvus service singleton instance"""
    global _milvus_service
    if _milvus_service is None:
        _milvus_service = MilvusService()
    return _milvus_service
