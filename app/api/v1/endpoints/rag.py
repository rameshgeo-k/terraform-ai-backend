"""
RAG Endpoints
Document management and RAG-enhanced chat
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json
import time
import logging

from app.schemas.requests import (
    RAGDocumentRequest,
    RAGQueryRequest,
    RAGChatRequest,
    RAGDocument,
    RAGQueryResponse,
    RAGChatResponse
)
from app.services.ollama import OllamaService
from app.services.rag import RAGService
from app.utils.helpers import sanitize_input, log_request

router = APIRouter()
logger = logging.getLogger(__name__)


def get_ollama_service() -> OllamaService:
    """Dependency injection for Ollama service"""
    from app.main import ollama_service
    return ollama_service


def get_rag_service() -> RAGService:
    """Dependency injection for RAG service"""
    from app.main import rag_service
    return rag_service


@router.post("/documents")
async def add_document(
    request: RAGDocumentRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Add document to RAG system"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        doc_id = rag.add_document(
            text=sanitize_input(request.text),
            doc_id=request.id,
            metadata=request.metadata
        )
        
        return {"id": doc_id, "status": "added"}
    
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    rag: RAGService = Depends(get_rag_service)
):
    """Get document by ID"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    document = rag.get_document(doc_id)
    
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.put("/documents/{doc_id}")
async def update_document(
    doc_id: str,
    request: RAGDocumentRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Update existing document"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    success = rag.update_document(
        doc_id=doc_id,
        text=sanitize_input(request.text),
        metadata=request.metadata
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or update failed")
    
    return {"id": doc_id, "status": "updated"}


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    rag: RAGService = Depends(get_rag_service)
):
    """Delete document by ID"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    success = rag.delete_document(doc_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"id": doc_id, "status": "deleted"}


@router.get("/documents")
async def list_documents(
    limit: int = 10,
    offset: int = 0,
    rag: RAGService = Depends(get_rag_service)
):
    """List documents with pagination"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    documents = rag.list_documents(limit=limit, offset=offset)
    
    return {
        "documents": documents,
        "limit": limit,
        "offset": offset
    }


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    rag: RAGService = Depends(get_rag_service)
):
    """Semantic search for documents"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    try:
        results = rag.query(
            query_text=sanitize_input(request.query),
            top_k=request.top_k
        )
        
        return {"results": results}
    
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=RAGChatResponse)
async def rag_chat(
    request: RAGChatRequest,
    ollama: OllamaService = Depends(get_ollama_service),
    rag: RAGService = Depends(get_rag_service)
):
    """RAG-enhanced chat: retrieve context and generate response"""
    if rag is None or ollama is None:
        raise HTTPException(status_code=503, detail="RAG or Ollama service not initialized")
    
    start_time = time.time()
    
    try:
        # Build context from retrieved documents
        context = rag.build_rag_context(
            query=sanitize_input(request.query),
            top_k=request.top_k
        )
        
        # Build messages with context
        messages = []
        if context:
            messages.append({
                "role": "system",
                "content": f"Use the following context to answer the user's question:\n\n{context}"
            })
        messages.append({
            "role": "user",
            "content": request.query
        })
        
        # Estimate input tokens
        full_text = context + " " + request.query
        input_tokens = ollama.count_tokens(full_text)
        
        if request.stream:
            # Streaming response
            async def generate():
                try:
                    streamer = await ollama.chat(
                        messages=messages,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        stream=True
                    )
                    
                    async for text in streamer:
                        chunk = {
                            "id": f"rag-{int(time.time())}",
                            "object": "rag.chat.chunk",
                            "created": int(time.time()),
                            "delta": {"content": text}
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"RAG streaming error: {e}")
                    yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        else:
            # Non-streaming response
            result = await ollama.chat(
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=False
            )
            
            generated_text = result['content']
            output_tokens = result.get('eval_count', ollama.count_tokens(generated_text))
            prompt_tokens = result.get('prompt_eval_count', input_tokens)
            inference_time = time.time() - start_time
            
            # Log request
            log_request(
                endpoint="/v1/rag/chat",
                input_tokens=prompt_tokens,
                output_tokens=output_tokens,
                inference_time=inference_time
            )
            
            return {
                "id": f"rag-{int(time.time())}",
                "object": "rag.chat.completion",
                "created": int(time.time()),
                "response": generated_text,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": prompt_tokens + output_tokens
                }
            }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"RAG chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_rag_stats(rag: RAGService = Depends(get_rag_service)):
    """Get RAG collection statistics"""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG service not initialized")
    
    return rag.get_stats()
