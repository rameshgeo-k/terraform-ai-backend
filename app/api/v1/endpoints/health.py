"""
Health Check Endpoint
System health and status monitoring
"""

from fastapi import APIRouter, Depends
from app.schemas.requests import HealthResponse
from app.services.ollama import OllamaService
from app.services.rag import RAGService

router = APIRouter()


def get_ollama_service() -> OllamaService:
    """Dependency injection for Ollama service"""
    from app.main import ollama_service
    return ollama_service


def get_rag_service() -> RAGService:
    """Dependency injection for RAG service"""
    from app.main import rag_service
    return rag_service


@router.get("/health", response_model=HealthResponse)
async def health_check(
    ollama: OllamaService = Depends(get_ollama_service),
    rag: RAGService = Depends(get_rag_service)
):
    """Health check endpoint"""
    ollama_healthy = await ollama.health_check() if ollama else False
    
    return {
        "status": "healthy" if ollama_healthy else "degraded",
        "ollama_connected": ollama_healthy,
        "rag_initialized": rag is not None
    }
