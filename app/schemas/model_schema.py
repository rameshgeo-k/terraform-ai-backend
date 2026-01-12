"""
Pydantic schemas for model configuration operations.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ModelConfigBase(BaseModel):
    """Base model configuration schema."""
    name: str = Field(..., min_length=1, max_length=100)
    model_type: str = Field(..., description="Type of model: chat, terraform, code")
    provider: str = Field(..., description="Provider: openai, anthropic, local")
    model_identifier: str = Field(..., description="Model ID: gpt-4, claude-3, etc.")
    api_endpoint: Optional[str] = None
    api_key_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ModelConfigCreate(ModelConfigBase):
    """Schema for creating a new model configuration."""
    is_active: bool = True


class ModelConfigUpdate(BaseModel):
    """Schema for updating model configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model_type: Optional[str] = None
    provider: Optional[str] = None
    model_identifier: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ModelConfigResponse(ModelConfigBase):
    """Schema for model configuration response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
