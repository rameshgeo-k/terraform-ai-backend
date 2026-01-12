"""
Utility Functions
Validation, sanitization, and helper functions
"""

import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def validate_prompt(prompt: str, max_length: int = 4096) -> bool:
    """Validate prompt length and content"""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    if len(prompt) > max_length * 4:
        raise ValueError(f"Prompt too long. Maximum ~{max_length} tokens allowed")
    
    return True


def sanitize_input(text: str) -> str:
    """Basic input sanitization"""
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Strip excessive whitespace
    text = ' '.join(text.split())
    
    return text


def log_request(
    endpoint: str,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    inference_time: Optional[float] = None,
    status_code: int = 200,
    error: Optional[str] = None
) -> None:
    """Log API request with metrics"""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": endpoint,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": (input_tokens or 0) + (output_tokens or 0),
        "inference_time": inference_time,
        "status_code": status_code,
    }
    
    if error:
        log_data["error"] = error
        logger.error(f"Request failed: {json.dumps(log_data)}")
    else:
        logger.info(f"Request completed: {json.dumps(log_data)}")
