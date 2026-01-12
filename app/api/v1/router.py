"""
API Router
Combines all v1 endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, chat, rag

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(chat.router, prefix="/v1", tags=["chat"])
api_router.include_router(rag.router, prefix="/v1/rag", tags=["rag"])
