"""
File Upload Endpoints
Handle file uploads and storage in RAG
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import Optional, List
import logging
import uuid
from datetime import datetime

from app.schemas.requests import FileUploadResponse, FileListResponse
from app.services.rag import RAGService
from app.utils.file_processor import FileProcessor

router = APIRouter()
logger = logging.getLogger(__name__)


def get_rag_service() -> RAGService:
    """Dependency injection for RAG service"""
    from app.main import rag_service
    return rag_service


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    store_in_rag: bool = Form(True),
    metadata: Optional[str] = Form(None),
    rag: RAGService = Depends(get_rag_service)
):
    """
    Upload file and optionally store in RAG
    
    - **file**: File to upload (PDF, DOCX, TXT, code files, etc.)
    - **store_in_rag**: Whether to store extracted text in RAG (default: True)
    - **metadata**: Optional JSON metadata string
    """
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        # Validate file type
        if not FileProcessor.is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported: {', '.join(FileProcessor.SUPPORTED_EXTENSIONS.keys())}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size (10MB default limit)
        if not FileProcessor.validate_file_size(file_size, max_size_mb=10):
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 10MB limit"
            )
        
        # Extract text from file
        extraction_result = await FileProcessor.extract_text(
            file_content=file_content,
            filename=file.filename
        )
        
        doc_id = str(uuid.uuid4())
        extracted_text = extraction_result['text']
        
        # Prepare metadata
        import json
        file_metadata = extraction_result['metadata']
        file_metadata['uploaded_at'] = datetime.utcnow().isoformat()
        file_metadata['doc_id'] = doc_id
        file_metadata['format'] = extraction_result['format']
        
        if metadata:
            try:
                custom_metadata = json.loads(metadata)
                file_metadata.update(custom_metadata)
            except json.JSONDecodeError:
                logger.warning(f"Invalid metadata JSON: {metadata}")
        
        # Store in RAG if requested
        if store_in_rag:
            stored_id = rag.add_document(
                text=extracted_text,
                doc_id=doc_id,
                metadata=file_metadata
            )
            
            logger.info(f"File {file.filename} stored in RAG with ID: {stored_id}")
            
            return {
                "id": stored_id,
                "filename": file.filename,
                "size": file_size,
                "format": extraction_result['format'],
                "stored_in_rag": True,
                "message": "File uploaded and stored in RAG successfully",
                "metadata": file_metadata
            }
        else:
            return {
                "id": doc_id,
                "filename": file.filename,
                "size": file_size,
                "format": extraction_result['format'],
                "stored_in_rag": False,
                "message": "File processed successfully (not stored in RAG)",
                "metadata": file_metadata
            }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@router.get("/files", response_model=FileListResponse)
async def list_files(
    limit: int = 10,
    offset: int = 0,
    rag: RAGService = Depends(get_rag_service)
):
    """
    List uploaded files stored in RAG
    
    - **limit**: Maximum number of files to return
    - **offset**: Number of files to skip
    """
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        documents = rag.list_documents(limit=limit, offset=offset)
        stats = rag.get_stats()
        
        # Filter to only show uploaded files (those with filename in metadata)
        files = [
            {
                "id": doc["id"],
                "filename": doc["metadata"].get("filename", "unknown"),
                "uploaded_at": doc["metadata"].get("uploaded_at"),
                "format": doc["metadata"].get("format", "unknown"),
                "size": doc["metadata"].get("size", 0)
            }
            for doc in documents
            if "filename" in doc["metadata"]
        ]
        
        return {
            "files": files,
            "total": stats["total_documents"]
        }
    
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    rag: RAGService = Depends(get_rag_service)
):
    """
    Delete uploaded file from RAG
    
    - **file_id**: ID of the file to delete
    """
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        success = rag.delete_document(file_id)
        
        if success:
            return {
                "message": f"File {file_id} deleted successfully",
                "id": file_id
            }
        else:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_id}")
async def get_file(
    file_id: str,
    rag: RAGService = Depends(get_rag_service)
):
    """
    Get file information and content from RAG
    
    - **file_id**: ID of the file to retrieve
    """
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        document = rag.get_document(file_id)
        
        if document:
            return {
                "id": document["id"],
                "filename": document["metadata"].get("filename", "unknown"),
                "text": document["text"],
                "metadata": document["metadata"]
            }
        else:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    except Exception as e:
        logger.error(f"Error retrieving file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
