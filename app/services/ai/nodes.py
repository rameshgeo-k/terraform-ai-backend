"""
LangGraph node functions for AI operations (matches smart-chat-lambda pattern).
"""
from typing import List
from sqlalchemy.orm import Session
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.services.ai.graphs import ChatState, TerraformState
from app.services.chat_history_service import get_recent_messages, save_chat_message
from app.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def to_langchain_messages(messages: List[dict]) -> List[BaseMessage]:
    """Convert message dicts to LangChain message objects."""
    result = []
    for m in messages:
        role = m.get("role", "").lower()
        content = m.get("content", "")
        if not content:
            continue
        if role == "user":
            result.append(HumanMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
    return result


def create_conversation_identify_node(db: Session):
    """Create conversation identification node (Step 1)."""
    def conversation_identify(state: ChatState) -> ChatState:
        customer_id = state.get("customer_id")
        messages = state.get("messages", [])
        
        # Check if we have messages
        if not messages:
            logger.warning(f"[Node] Empty message in state for customer={customer_id}")
        
        return {
            "messages": messages,
            "input_type": "text",
            "history_loaded": False
        }
    
    return conversation_identify


def create_llm_interaction_node(db: Session):
    """Create LLM interaction node with history (Step 2)."""
    def llm_interaction(state: ChatState) -> ChatState:
        customer_id = state.get("customer_id")
        current_messages = state.get("messages", [])
        history_loaded = state.get("history_loaded", False)
        
        # Load history from database if not already loaded
        memory_messages = []
        if not history_loaded:
            db_messages = get_recent_messages(db, customer_id)
            logger.info(f"[LLM] Loaded {len(db_messages)} messages from DB for customer {customer_id}")
            
            if db_messages:
                memory_messages = to_langchain_messages(db_messages)
        
        # Combine memory and current messages
        all_messages = memory_messages + current_messages
        
        return {
            **state,
            "messages": all_messages,
            "memory": memory_messages
        }
    
    return llm_interaction


def create_response_handler_node():
    """Create response handler node (Step 3)."""
    def response_handler(state: ChatState) -> ChatState:
        return {
            "messages": state["messages"],
            "memory": state.get("messages", [])
        }
    
    return response_handler


def create_generate_node(llm: BaseChatModel):
    """
    Create a Terraform generation node function.
    
    Args:
        llm: Initialized LangChain model
        
    Returns:
        Generate node function
    """
    async def generate_node(state: TerraformState):
        """Generate Terraform code."""
        messages = state["messages"]
        response = await llm.ainvoke(messages)
        
        code = None
        if hasattr(response, 'content'):
            code = response.content.strip()
        elif response:
            code = str(response).strip()
        
        return {
            "messages": messages + [response],
            "generated_code": code
        }
    
    return generate_node
