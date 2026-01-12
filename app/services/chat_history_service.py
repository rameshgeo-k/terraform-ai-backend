"""
Chat History Service
Manages chat message persistence with light history (10 messages, 24hr expiry)
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.chat_message import ChatMessage
from app.constants.ai_constants import MAX_HISTORY_MESSAGES, HISTORY_EXPIRY_HOURS


async def save_message(
    db: Session,
    customer_id: int,
    role: str,
    content: str,
    model_used: Optional[str] = None
) -> ChatMessage:
    """
    Save a chat message to the database.
    
    Args:
        db: Database session
        customer_id: ID of the customer
        role: Message role ('user' or 'assistant')
        content: Message content
        model_used: AI model identifier used for the response
        
    Returns:
        Created ChatMessage instance
    """
    message = ChatMessage(
        customer_id=customer_id,
        role=role,
        content=content,
        model_used=model_used,
        created_at=datetime.utcnow()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_recent_messages(
    db: Session,
    customer_id: int,
    limit: int = MAX_HISTORY_MESSAGES,
) -> List[dict]:
    """
    Get recent chat messages for a customer as dicts.
    
    Args:
        db: Database session
        customer_id: ID of the customer
        limit: Maximum number of messages to retrieve (default 10)
        
    Returns:
        List of message dicts with 'role' and 'content' keys
    """
    messages = db.query(ChatMessage)\
        .filter(ChatMessage.customer_id == customer_id)\
        .order_by(desc(ChatMessage.created_at))\
        .limit(limit)\
        .all()
    
    # Return in chronological order (oldest to newest) for chat display
    return [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(messages)
    ]


async def cleanup_old_messages(
    db: Session,
    hours: int = HISTORY_EXPIRY_HOURS,
) -> int:
    """
    Delete chat messages older than specified hours.
    
    Args:
        db: Database session
        hours: Age threshold in hours (default 24)
        
    Returns:
        Number of messages deleted
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    deleted_count = db.query(ChatMessage)\
        .filter(ChatMessage.created_at < cutoff_time)\
        .delete()
    
    db.commit()
    return deleted_count


async def get_conversation_context(
    db: Session,
    customer_id: int,
    limit: int = MAX_HISTORY_MESSAGES,
) -> List[dict]:
    """
    Get recent messages formatted for AI context.
    
    Args:
        db: Database session
        customer_id: ID of the customer
        limit: Maximum number of messages to retrieve
        
    Returns:
        List of dicts with 'role' and 'content' keys
    """
    return get_recent_messages(db, customer_id, limit)


# Alias for compatibility
save_chat_message = save_message
get_recent_messages_dict = get_conversation_context
