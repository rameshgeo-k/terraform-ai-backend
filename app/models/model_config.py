"""
Model configuration for AI models (Chat AI, Terraform AI).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from app.core.database import Base


class ModelConfig(Base):
    """Model configuration database model."""
    __tablename__ = "model_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # e.g., "Chat AI", "Terraform AI"
    model_type = Column(String, nullable=False)  # e.g., "chat", "terraform", "code"
    provider = Column(String, nullable=False)  # e.g., "openai", "anthropic", "local"
    model_identifier = Column(String, nullable=False)  # e.g., "gpt-4", "claude-3"
    api_endpoint = Column(String)
    api_key_name = Column(String)  # Reference to secrets manager or env var
    parameters = Column(JSON)  # Model-specific parameters (temperature, max_tokens, etc.)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ModelConfig(id={self.id}, name='{self.name}', type='{self.model_type}')>"
