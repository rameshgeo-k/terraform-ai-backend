"""
Chat message model for storing conversation history.
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class ChatMessage(Base):
    """Chat message database model."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    model_used = Column(String(100))  # Which AI model generated the response (for assistant messages)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    customer = relationship("Customer", backref="chat_messages")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_customer_created', 'customer_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, customer_id={self.customer_id}, role='{self.role}')>"
    
    @classmethod
    def is_expired(cls, message_time: datetime, hours: int = 24) -> bool:
        """Check if message is older than specified hours."""
        return datetime.utcnow() - message_time > timedelta(hours=hours)
