"""
Request/Response Schemas
Pydantic models for API validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


class FileAttachment(BaseModel):
    """File attachment metadata"""
    filename: str
    content: str  # Base64 encoded file content or extracted text
    mime_type: Optional[str] = None
    size: Optional[int] = None


class Message(BaseModel):
    """Chat message"""
    role: Literal["system", "user", "assistant"]
    content: str
    attachments: Optional[List[FileAttachment]] = None


class ChatCompletionRequest(BaseModel):
    """Chat completion request"""
    messages: List[Message]
    stream: bool = False
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0, le=4096)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(None, gt=0)


class Choice(BaseModel):
    """Response choice"""
    index: int
    message: Message
    finish_reason: str


class Usage(BaseModel):
    """Token usage"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Chat completion response"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage


class RAGDocumentRequest(BaseModel):
    """Request to add/update RAG document"""
    id: Optional[str] = None
    text: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class RAGQueryRequest(BaseModel):
    """Request to query RAG"""
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(None, gt=0, le=20)


class RAGChatRequest(BaseModel):
    """Request for RAG-enhanced chat"""
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(None, gt=0, le=10)
    stream: bool = False
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0, le=4096)


class RAGDocument(BaseModel):
    """RAG document"""
    id: str
    text: str
    score: Optional[float] = None
    metadata: Dict[str, Any] = {}


class RAGQueryResponse(BaseModel):
    """Response from RAG query"""
    results: List[RAGDocument]


class RAGChatResponse(BaseModel):
    """Response from RAG chat"""
    id: str
    object: str = "rag.chat.completion"
    created: int
    response: str
    usage: Usage


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    ollama_connected: bool
    rag_initialized: bool


class ModelInfo(BaseModel):
    """Model information"""
    id: str
    type: str
    base_model: str
    adapter: str
    format: str
    backend: str
    loaded: bool
    size: int
    modified_at: str


class ModelsResponse(BaseModel):
    """Models list response"""
    object: str = "list"
    data: List[ModelInfo]


class FileUploadResponse(BaseModel):
    """File upload response"""
    id: str
    filename: str
    size: int
    format: str
    stored_in_rag: bool
    message: str
    metadata: Dict[str, Any] = {}


class FileListResponse(BaseModel):
    """List of uploaded files"""
    files: List[Dict[str, Any]]
    total: int
