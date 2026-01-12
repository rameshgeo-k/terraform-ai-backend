"""
API Router
Combines all v1 endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, chat, rag, files, admin

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(chat.router, prefix="/v1", tags=["chat"])
api_router.include_router(rag.router, prefix="/v1/rag", tags=["rag"])
api_router.include_router(files.router, prefix="/v1/files", tags=["files"])
api_router.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
