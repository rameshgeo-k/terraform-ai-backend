"""
AI Chat routes for infrastructure assistance with LangChain streaming.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.ai.chat_service import stream_chat_response
from app.services.chat_history_service import save_message, get_conversation_context
from app.api.routes.customers import get_customer_from_token
from app.models.model_config import ModelConfig
from app.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str


async def generate_sse_response(
    db: Session,
    message: str,
    customer_id: int
):
    """
    Generate Server-Sent Events stream for chat response.
    
    Args:
        db: Database session
        message: User message
        customer_id: Customer ID
        
    Yields:
        SSE formatted chunks
    """
    try:
        # Save user message to history
        await save_message(
            db=db,
            customer_id=customer_id,
            role="user",
            content=message
        )
        
        # Get recent conversation context (last 10 messages)
        history = await get_conversation_context(db, customer_id, limit=9)
        
        # Stream the AI response
        full_response = ""
        model_used = None
        
        # Get the model name for saving
        from app.models.model_config import ModelConfig
        chat_model = db.query(ModelConfig).filter(
            ModelConfig.model_type == "both",
            ModelConfig.is_active == True
        ).first()
        
        if not chat_model:
            chat_model = db.query(ModelConfig).filter(
                ModelConfig.model_type == "chat",
                ModelConfig.is_active == True
            ).first()
        
        model_used = chat_model.name if chat_model else "no-model"
        
        async for chunk in stream_chat_response(db, message, customer_id, history):
            # Handle error messages
            if chunk.startswith("ERROR:"):
                yield f"data: {chunk}\n\n"
                return
            
            full_response += chunk
            # Send chunk as SSE event
            yield f"data: {chunk}\n\n"
        
        # Save assistant response to history
        await save_message(
            db=db,
            customer_id=customer_id,
            role="assistant",
            content=full_response,
            model_used=model_used
        )
        
        # Send end marker
        yield "data: [DONE]\n\n"
    
    except Exception as e:
        logger.error(f"Chat streaming error: {str(e)}")
        error_msg = str(e)
        
        if "quota" in error_msg.lower():
            yield f"data: ERROR: AI quota exceeded. Contact administrator.\n\n"
        elif "authentication" in error_msg.lower():
            yield f"data: ERROR: Authentication failed. Invalid API key.\n\n"
        elif "not found" in error_msg.lower():
            yield f"data: ERROR: Model not available.\n\n"
        else:
            yield f"data: ERROR: {error_msg[:100]}\n\n"
        
        yield "data: [DONE]\n\n"


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_customer = Depends(get_customer_from_token)
):
    """
    Send a message to the AI assistant and get a streaming response.
    Uses Server-Sent Events (SSE) for real-time token streaming.
    
    Args:
        request: Chat message from user
        db: Database session
        current_customer: Current authenticated customer
        
    Returns:
        StreamingResponse with SSE formatted chunks
    """
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    return StreamingResponse(
        generate_sse_response(db, request.message, current_customer.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
