"""
Terraform AI Assistant API
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional

from app.core.config import settings
from app.core.logging import setup_logging
from app.services.ollama import OllamaService
from app.services.rag import RAGService
from app.api.v1.router import api_router

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Global service instances
ollama_service: Optional[OllamaService] = None
rag_service: Optional[RAGService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global ollama_service, rag_service
    
    # Startup
    logger.info("Starting Terraform AI Assistant API...")
    
    try:
        # Initialize Ollama service
        logger.info("Initializing Ollama service...")
        ollama_service = OllamaService()
        
        # Health check
        is_healthy = await ollama_service.health_check()
        if not is_healthy:
            logger.warning("Ollama service may not be running. Start it with: ollama serve")
        else:
            logger.info("Ollama service is running")
        
        # Initialize RAG service
        logger.info("Initializing RAG service...")
        rag_service = RAGService()
        
        logger.info("Server initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down server...")
    if ollama_service:
        await ollama_service.close()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Production-ready AI server with CodeLlama-7b and RAG capabilities",
    version=settings.app_version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        log_level=settings.server.log_level
    )
