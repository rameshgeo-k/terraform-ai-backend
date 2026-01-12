"""
RAG Service
Document storage, retrieval, and semantic search using ChromaDB
"""

import os
import sys
import logging
import uuid
from typing import List, Dict, Any, Optional

# MUST disable telemetry BEFORE importing chromadb
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Monkey-patch posthog to completely disable telemetry
try:
    import posthog
    
    class NoOpPosthog:
        """No-op Posthog replacement to disable telemetry"""
        def __init__(self, *args, **kwargs):
            pass
        
        def capture(self, *args, **kwargs):
            pass
        
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    sys.modules['posthog'] = NoOpPosthog()
except ImportError:
    pass

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG operations with ChromaDB"""
    
    def __init__(self):
        """Initialize RAG service with ChromaDB and embedding model"""
        # Initialize ChromaDB client
        persist_directory = settings.rag.chroma_persist_directory
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                allow_reset=True,
                is_persistent=True
            )
        )
        
        # Load embedding model
        embedding_model_name = settings.rag.embedding_model
        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Get or create collection
        collection_name = settings.rag.collection_name
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Using existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Document collection for RAG"}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        self.default_top_k = settings.rag.default_top_k
    
    # Document Management Methods
    
    def add_document(
        self,
        text: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add document to ChromaDB
        
        Args:
            text: Document text content
            doc_id: Optional document ID (auto-generated if not provided)
            metadata: Optional metadata dictionary
            
        Returns:
            Document ID
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        embedding = self.embedding_model.encode(text).tolist()
        
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}]
        )
        
        logger.info(f"Added document: {doc_id}")
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID
        
        Args:
            doc_id: Document ID to retrieve
            
        Returns:
            Document dict with id, text, and metadata, or None if not found
        """
        try:
            result = self.collection.get(ids=[doc_id])
            
            if result['ids']:
                return {
                    "id": result['ids'][0],
                    "text": result['documents'][0],
                    "metadata": result['metadatas'][0] if result['metadatas'] else {}
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
            return None
    
    def update_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update existing document
        
        Args:
            doc_id: Document ID to update
            text: New document text
            metadata: Optional new metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            embedding = self.embedding_model.encode(text).tolist()
            
            self.collection.update(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}]
            )
            
            logger.info(f"Updated document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document by ID
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def list_documents(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List documents in collection
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of document dictionaries
        """
        try:
            result = self.collection.get()
            
            start = offset
            end = offset + limit
            
            documents = []
            if result['ids']:
                for i in range(start, min(end, len(result['ids']))):
                    if i < len(result['ids']):
                        documents.append({
                            "id": result['ids'][i],
                            "text": result['documents'][i],
                            "metadata": result['metadatas'][i] if result['metadatas'] else {}
                        })
            
            return documents
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    # Query and Search Methods
    
    def query(
        self,
        query_text: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant documents
        
        Args:
            query_text: Search query text
            top_k: Number of results to return (defaults to config value)
            
        Returns:
            List of matching documents with similarity scores
        """
        if top_k is None:
            top_k = self.default_top_k
        
        query_embedding = self.embedding_model.encode(query_text).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        documents = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                documents.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "score": 1 - results['distances'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                })
        
        logger.info(f"Query returned {len(documents)} results")
        return documents
    
    def build_rag_context(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> str:
        """
        Build context string from retrieved documents for RAG
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            
        Returns:
            Formatted context string for LLM prompt
        """
        results = self.query(query, top_k)
        
        if not results:
            return ""
        
        context_parts = ["Retrieved Context:"]
        for i, doc in enumerate(results, 1):
            context_parts.append(f"\n[{i}] {doc['text']}")
        
        context_parts.append("\n\nBased on the above context, please answer the following:")
        
        return "\n".join(context_parts)
    
    # Collection Statistics
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection.name
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"total_documents": 0, "error": str(e)}
