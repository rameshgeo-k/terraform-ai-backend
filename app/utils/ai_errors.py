"""
Error handling utilities for AI services.
"""
from typing import Optional
from app.utils.logging_utils import setup_logger

logger = setup_logger(__name__)


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class QuotaExceededError(AIServiceError):
    """Raised when AI service quota is exceeded."""
    pass


class AuthenticationError(AIServiceError):
    """Raised when AI service authentication fails."""
    pass


class ModelNotFoundError(AIServiceError):
    """Raised when the specified model is not found."""
    pass


class PaymentRequiredError(AIServiceError):
    """Raised when payment method is required."""
    pass


class RateLimitError(AIServiceError):
    """Raised when rate limit is exceeded."""
    pass


def parse_ai_error(error: Exception, model_id: Optional[str] = None) -> str:
    """
    Parse AI service errors and return user-friendly messages.
    
    Args:
        error: The exception that occurred
        model_id: Optional model identifier for context
        
    Returns:
        User-friendly error message
    """
    error_str = str(error)
    
    # Quota errors
    if "quota" in error_str.lower() or "insufficient_quota" in error_str.lower():
        return "AI service quota exceeded. Please contact administrator to add credits."
    
    # Authentication errors
    if "401" in error_str or "authentication" in error_str.lower() or "api key" in error_str.lower():
        return "Authentication failed. Invalid or missing API key."
    
    # Model not found
    if "404" in error_str or ("model" in error_str.lower() and "not found" in error_str.lower()):
        msg = f"Model not available"
        if model_id:
            msg += f": {model_id}"
        return msg
    
    # AWS Bedrock specific errors
    if "ResourceNotFoundException" in error_str:
        if "use case details have not been submitted" in error_str.lower():
            return (
                "Anthropic use case form required. Go to AWS Bedrock console → "
                "Model catalog → Select Claude model → Open in Playground → "
                "Submit use case details. Wait 15 minutes after submission."
            )
        return "Model not found in AWS Bedrock. Verify model ID and region."
    
    # Payment/billing errors
    if "INVALID_PAYMENT_INSTRUMENT" in error_str:
        return (
            "AWS payment method required. Add a valid payment method: "
            "AWS Console → Billing → Payment methods. Wait 15 minutes after adding."
        )
    
    if "AWS Marketplace subscription" in error_str:
        return "AWS Marketplace subscription incomplete. Check payment method in Billing console."
    
    # Access denied
    if "AccessDeniedException" in error_str:
        return "Access denied. Check IAM permissions (bedrock:InvokeModel, bedrock:InvokeModelWithResponseStream)."
    
    # Rate limiting
    if "ThrottlingException" in error_str or "rate limit" in error_str.lower():
        return "Rate limit exceeded. Please try again in a few moments."
    
    # Validation errors
    if "ValidationException" in error_str:
        if "model identifier is invalid" in error_str.lower():
            return (
                "Invalid Bedrock model ID. Use format: "
                "anthropic.claude-3-sonnet-20240229-v1:0 or "
                "anthropic.claude-3-haiku-20240307-v1:0"
            )
        return "Invalid request parameters. Check model configuration."
    
    # Generic error
    return f"AI service error: {error_str[:150]}"


def get_error_prefix(error_str: str) -> str:
    """
    Get appropriate error prefix based on error type.
    
    Args:
        error_str: Error string to analyze
        
    Returns:
        Error prefix emoji/text
    """
    if "quota" in error_str.lower():
        return "💳"
    elif "authentication" in error_str.lower():
        return "🔑"
    elif "not found" in error_str.lower():
        return "❌"
    elif "payment" in error_str.lower():
        return "💰"
    elif "rate limit" in error_str.lower():
        return "⏱️"
    else:
        return "⚠️"
