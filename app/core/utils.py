"""
Utility functions for the application.
"""
import logging
from typing import Any, Dict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO 8601 string."""
    return dt.isoformat() if dt else None


def sanitize_dict(data: Dict[str, Any], exclude_keys: list = None) -> Dict[str, Any]:
    """
    Remove sensitive keys from a dictionary.
    
    Args:
        data: Dictionary to sanitize
        exclude_keys: List of keys to remove
        
    Returns:
        Sanitized dictionary
    """
    if exclude_keys is None:
        exclude_keys = ['password', 'hashed_password', 'secret', 'token']
    
    return {k: v for k, v in data.items() if k not in exclude_keys}


def parse_terraform_output(output: str) -> Dict[str, Any]:
    """
    Parse Terraform command output.
    
    Args:
        output: Raw terraform output string
        
    Returns:
        Parsed output dictionary
    """
    # TODO: Implement actual parsing logic
    return {
        "raw_output": output,
        "parsed_at": datetime.utcnow().isoformat()
    }
