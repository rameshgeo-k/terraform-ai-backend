"""
Chat service using LangChain and LangGraph (matches smart-chat-lambda pattern).
"""
from typing import AsyncGenerator, List, Dict, Optional, Callable
from sqlalchemy.orm import Session

from langchain_core.messages import HumanMessage, SystemMessage, BaseMessageChunk, AIMessage

from app.constants.ai_constants import INFRASTRUCTURE_SYSTEM_PROMPT
from app.services.ai.model_factory import ModelFactory, get_active_model
from app.services.ai.graphs import create_chat_graph
from app.services.ai.nodes import (
    create_conversation_identify_node,
    create_llm_interaction_node,
    create_response_handler_node,
)
from app.services.chat_history_service import save_chat_message
from app.utils.ai_errors import parse_ai_error
from app.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def stream_response_collector(
    stream,
    collector: List[str],
    on_complete: Optional[Callable[[str, Optional[dict]], None]] = None,
):
    """
    Collect streamed response chunks (matches smart-chat-lambda).
    
    Args:
        stream: LLM stream iterator
        collector: List to collect chunks
        on_complete: Callback when stream completes
        
    Yields:
        Text chunks from stream
    """
    response_metadata = None
    usage_metadata = None
    
    for chunk in stream:
        text = None
        if hasattr(chunk, "response_metadata"):
            response_metadata = chunk.response_metadata
        if hasattr(chunk, "usage_metadata"):
            usage_metadata = chunk.usage_metadata
        if hasattr(chunk, "content") and isinstance(chunk.content, list):
            text_parts = [
                part.get("text", "")
                for part in chunk.content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            text = "".join(text_parts)
        elif hasattr(chunk, "content") and isinstance(chunk.content, str):
            text = chunk.content
        else:
            text = str(chunk)
        
        if text:
            collector.append(text)
            yield text
    
    if on_complete:
        on_complete(
            "".join(collector),
            {
                "response_metadata": response_metadata,
                "usage_metadata": usage_metadata,
            }
        )


async def stream_chat_response(
    db: Session,
    message: str,
    customer_id: int,
    history: List[Dict] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream AI chat response using LangGraph (matches smart-chat-lambda).
    
    Args:
        db: Database session
        message: User message
        customer_id: Customer ID
        history: Previous conversation history (optional, loaded from DB)
        
    Yields:
        Token chunks from AI response
    """
    # Get active chat model
    chat_model = get_active_model(db, "chat")
    
    if not chat_model:
        logger.warning("No active chat AI model configured")
        yield "ERROR: No AI model configured. Please contact administrator."
        return
    
    try:
        # Initialize LangChain model
        llm = ModelFactory.create_from_config(chat_model)
        
        # Build the graph with nodes (smart-chat-lambda pattern)
        identify_node = create_conversation_identify_node(db)
        llm_node = create_llm_interaction_node(db)
        response_node = create_response_handler_node()
        graph = create_chat_graph(identify_node, llm_node, response_node)
        
        # Prepare initial state
        user_message = HumanMessage(content=message)
        state = {
            "customer_id": customer_id,
            "messages": [user_message],
        }
        
        # Invoke graph to process state
        logger.info(f"[Chat] Processing message for customer {customer_id}")
        final_state = graph.invoke(
            state,
            config={"configurable": {"thread_id": str(customer_id)}}
        )
        
        # Get processed messages from graph
        messages = final_state.get("messages", [])
        
        # Prepare messages for LLM with system prompt
        system_prompt = SystemMessage(content=INFRASTRUCTURE_SYSTEM_PROMPT)
        prepared_messages = [system_prompt] + messages
        
        logger.info(f"Streaming chat response for customer {customer_id} using {chat_model.name}")
        
        # Stream the response
        collector = []
        
        def on_complete(full_response: str, metadata: Optional[dict]):
            """Save response to database when stream completes."""
            if metadata:
                logger.info(f"[Stream Metadata] {metadata}")
            # Save assistant message to database (async function, but called sync in background)
            import asyncio
            try:
                asyncio.create_task(save_chat_message(
                    db=db,
                    customer_id=customer_id,
                    role="assistant",
                    content=full_response
                ))
            except RuntimeError:
                # If no event loop, run synchronously
                import inspect
                if inspect.iscoroutinefunction(save_chat_message):
                    asyncio.run(save_chat_message(
                        db=db,
                        customer_id=customer_id,
                        role="assistant",
                        content=full_response
                    ))
                else:
                    save_chat_message(
                        db=db,
                        customer_id=customer_id,
                        role="assistant",
                        content=full_response
                    )
        
        stream = llm.stream(
            input=prepared_messages,
            config={"configurable": {"thread_id": str(customer_id)}}
        )
        
        for chunk in stream_response_collector(stream, collector, on_complete):
            yield chunk
    
    except Exception as e:
        logger.error(f"Chat streaming error: {str(e)}", exc_info=True)
        error_msg = parse_ai_error(e, chat_model.model_identifier)
        yield f"ERROR: {error_msg}"


def build_message_history(history: List[Dict]) -> List:
    """
    Convert history dicts to LangChain message objects.
    
    Args:
        history: List of message dicts with 'role' and 'content'
        
    Returns:
        List of LangChain message objects
    """
    messages = []
    
    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "")
        
        if role == "system":
            messages.append(SystemMessage(content=content))
        elif role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    
    return messages
