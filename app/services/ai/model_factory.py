"""
LangChain model factory - handles initialization of AI models.
"""
import os
from typing import Optional
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_aws import ChatBedrock
from langchain_ollama import ChatOllama

from app.models.model_config import ModelConfig
from app.constants.ai_constants import (
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
)
from app.utils.logging_utils import setup_logger
from app.core.config import settings

logger = setup_logger(__name__)


class ModelFactory:
    """Factory for creating LangChain model instances."""
    
    @staticmethod
    def create_openai_model(
        model_id: str,
        api_key: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> ChatOpenAI:
        """
        Create OpenAI chat model.
        
        Args:
            model_id: OpenAI model identifier
            api_key: API key (will use env var if not provided)
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Configured ChatOpenAI instance
            
        Raises:
            ValueError: If API key is not configured
        """
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API key not configured in model settings or environment")
        
        logger.info(f"Initializing OpenAI model: {model_id}")
        
        return ChatOpenAI(
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            streaming=True,
        )
    
    @staticmethod
    def create_anthropic_model(
        model_id: str,
        api_key: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> ChatAnthropic:
        """
        Create Anthropic chat model.
        
        Args:
            model_id: Anthropic model identifier
            api_key: API key (will use env var if not provided)
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Configured ChatAnthropic instance
            
        Raises:
            ValueError: If API key is not configured
        """
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("Anthropic API key not configured in model settings or environment")
        
        logger.info(f"Initializing Anthropic model: {model_id}")
        
        return ChatAnthropic(
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            streaming=True,
        )
    
    @staticmethod
    def create_ollama_model(
        model_id: str,
        base_url: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> ChatOllama:
        """
        Create Ollama chat model (local LLM).
        
        Args:
            model_id: Ollama model identifier (e.g., 'llama3.2', 'mistral')
            base_url: Ollama server URL (defaults to settings.OLLAMA_BASE_URL)
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Configured ChatOllama instance
        """
        if base_url is None:
            base_url = settings.OLLAMA_BASE_URL
        
        logger.info(f"Initializing Ollama model: {model_id} at {base_url}")
        
        return ChatOllama(
            model=model_id,
            base_url=base_url,
            temperature=temperature,
            num_predict=max_tokens,
        )
    
    @staticmethod
    def create_bedrock_model(
        model_id: str,
        provider: str,
        profile_arn: str,
        aws_region: str = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> ChatBedrock:
        """
        Create AWS Bedrock chat model.
        
        Args:
            model_id: Bedrock model identifier
            provider: Provider name (should be extracted from model_id, not "bedrock")
            profile_arn: AWS profile ARN
            aws_region: AWS region (defaults to settings.AWS_REGION if not provided)
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Configured ChatBedrock instance
        """
        # Use configured region if not explicitly provided
        if aws_region is None:
            aws_region = settings.AWS_REGION
        
        logger.info(f"Initializing Bedrock model: {model_id} (region: {aws_region}, provider: {provider})")
        
        # Use same pattern as smart-chat-lambda
        return ChatBedrock(
            model=profile_arn,
            provider=provider,
            region_name=aws_region,
            model_kwargs={
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            streaming=True,
        )
    
    @classmethod
    def create_from_config(cls, model_config: ModelConfig):
        """
        Create LangChain model from database configuration.
        
        Args:
            model_config: Model configuration from database
            
        Returns:
            Configured chat model instance
            
        Raises:
            ValueError: If provider is unsupported or configuration is invalid
        """
        params = model_config.parameters or {}
        temperature = params.get("temperature", DEFAULT_TEMPERATURE)
        max_tokens = params.get("max_tokens", DEFAULT_MAX_TOKENS)
        
        provider = model_config.provider.lower()
        model_id = model_config.model_identifier
        api_key = model_config.api_key_name
        
        try:
            if provider == "openai":
                return cls.create_openai_model(
                    model_id=model_id,
                    api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            
            elif provider == "anthropic":
                return cls.create_anthropic_model(
                    model_id=model_id,
                    api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            
            elif provider == "ollama":
                # Get Ollama base URL from params or settings
                base_url = params.get("base_url") or settings.OLLAMA_BASE_URL
                
                return cls.create_ollama_model(
                    model_id=model_id,
                    base_url=base_url,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            
            elif provider == "bedrock":
                # Get region from model config params, or fallback to settings
                aws_region = params.get("aws_region")
                profile_arn = params.get("profile_arn")  # Optional AWS profile ARN
                
                return cls.create_bedrock_model(
                    model_id=profile_arn,  # Use model_id, not api_key_name
                    provider=model_config.provider,
                    profile_arn=profile_arn,
                    aws_region=aws_region,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        
        except Exception as e:
            logger.error(f"Failed to initialize {provider} model '{model_id}': {str(e)}")
            raise


def get_active_model(db: Session, model_type: str) -> Optional[ModelConfig]:
    """
    Get active model configuration from database.
    
    Args:
        db: Database session
        model_type: Type of model ('chat', 'terraform', or 'both')
        
    Returns:
        Active model configuration or None
    """
    # Try 'both' first
    model = db.query(ModelConfig).filter(
        ModelConfig.model_type == "both",
        ModelConfig.is_active == True
    ).first()
    
    if model:
        logger.info(f"Using 'both' type model for {model_type}: {model.name}")
        return model
    
    # Fall back to specific type
    model = db.query(ModelConfig).filter(
        ModelConfig.model_type == model_type,
        ModelConfig.is_active == True
    ).first()
    
    if model:
        logger.info(f"Using '{model_type}' type model: {model.name}")
    else:
        logger.warning(f"No active {model_type} model configured")
    
    return model
