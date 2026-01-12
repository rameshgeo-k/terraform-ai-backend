"""
Admin authentication schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class AdminLogin(BaseModel):
    """Admin login request schema."""
    email: EmailStr
    password: str


class AdminCreate(BaseModel):
    """Admin creation schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class AdminUpdate(BaseModel):
    """Admin update schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class AdminResponse(BaseModel):
    """Admin response schema."""
    id: int
    email: str
    username: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
