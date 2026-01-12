"""
LangGraph state definitions and graph builders.
"""
from typing import List, Optional, TypedDict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver


class ChatState(TypedDict, total=False):
    """State for chat graph."""
    customer_id: int
    messages: List[BaseMessage]
    memory: Optional[List[BaseMessage]]
    input_type: Optional[str]
    history_loaded: Optional[bool]


class TerraformState(TypedDict):
    """State for terraform generation graph."""
    messages: List[BaseMessage]
    generated_code: Optional[str]


def create_chat_graph(identify_node, llm_node, response_node):
    """
    Create LangGraph StateGraph for chat (matches smart-chat-lambda).
    
    Args:
        identify_node: Message identification node
        llm_node: LLM interaction node
        response_node: Response handler node
        
    Returns:
        Compiled StateGraph with memory checkpointing
    """
    graph = StateGraph(ChatState)
    graph.add_node("conversation_identify", identify_node)
    graph.add_node("llm_interaction", llm_node)
    graph.add_node("response_handler", response_node)
    
    graph.add_edge(START, "conversation_identify")
    graph.add_edge("conversation_identify", "llm_interaction")
    graph.add_edge("llm_interaction", "response_handler")
    graph.add_edge("response_handler", END)
    
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


def create_terraform_graph(generate_node):
    """
    Create LangGraph StateGraph for Terraform generation.
    
    Args:
        generate_node: Generate node function
        
    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(TerraformState)
    workflow.add_node("generate", generate_node)
    workflow.set_entry_point("generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()
