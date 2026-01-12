"""
Terraform code generation service using LangChain and LangGraph.
"""
from typing import Optional
from sqlalchemy.orm import Session

from langchain_core.messages import HumanMessage, SystemMessage

from app.constants.ai_constants import TERRAFORM_SYSTEM_PROMPT
from app.services.ai.model_factory import ModelFactory, get_active_model
from app.services.ai.graphs import create_terraform_graph
from app.services.ai.nodes import create_generate_node
from app.schemas.terraform_schema import TerraformGenerateRequest
from app.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


def build_terraform_prompt(request: TerraformGenerateRequest) -> str:
    """
    Build a detailed prompt for AI terraform generation.
    
    Args:
        request: Generation request with project details
        
    Returns:
        Formatted prompt string
    """
    resource_list = "\n".join([
        f"- {r.label} ({r.type})" 
        for r in request.resources
    ])
    
    prompt = f"""Generate production-ready Terraform code for the following infrastructure:
    
    Project: {request.project_name}
    Cloud Provider: {request.provider.upper()}
    Description: {request.description or 'N/A'}

    Resources to create:
    {resource_list}

    Requirements:
    1. Include proper provider configuration
    2. Use appropriate resource types for {request.provider}
    3. Include tags with project name
    4. Follow Terraform best practices
    5. Add comments explaining each resource
    6. Use variables where appropriate
    7. Include outputs for important values

    Generate only the Terraform code, no explanations."""

    return prompt


async def generate_terraform_code(
    db: Session,
    request: TerraformGenerateRequest,
) -> Optional[str]:
    """
    Generate Terraform code using LangGraph AI.
    
    Args:
        db: Database session
        request: Terraform generation request
        
    Returns:
        Generated Terraform code or None if model not configured
    """
    # Get active terraform model
    terraform_model = get_active_model(db, "terraform")
    
    if not terraform_model:
        logger.info("No active terraform AI model configured")
        return None
    
    try:
        # Initialize LangChain model
        llm = ModelFactory.create_from_config(terraform_model)
        
        # Build prompt
        prompt = build_terraform_prompt(request)
        
        # Build messages
        messages = [
            SystemMessage(content=TERRAFORM_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        
        # Create graph with generate node
        generate_node = create_generate_node(llm)
        graph = create_terraform_graph(generate_node)
        
        # Get response using graph
        logger.info(f"Generating Terraform code for project: {request.project_name}")
        
        initial_state = {
            "messages": messages,
            "generated_code": None
        }
        
        result = await graph.ainvoke(initial_state)
        
        code = result.get("generated_code")
        
        if code:
            logger.info(f"Generated {len(code)} characters of Terraform code")
        
        return code
    
    except Exception as e:
        logger.error(f"Terraform generation error: {str(e)}", exc_info=True)
        return None
