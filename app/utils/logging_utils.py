"""
Logging Configuration
Structured logging setup with JSON and text formats
"""

import logging
import sys
from pathlib import Path

from pythonjsonlogger import jsonlogger
from app.core.config import settings

# Global flag to track if logging has been setup
_logging_configured = False


def setup_logging() -> None:
    """
    Setup application logging with console and file handlers.
    Supports both text and JSON formats.
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    log_level = settings.LOG_LEVEL.upper()
    log_format = settings.LOG_FORMAT.lower()
    log_dir = Path(settings.LOG_DIRECTORY)
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    logger.handlers.clear()  # Clear any existing handlers
    
    # Choose formatter based on configuration
    if log_format == 'json':
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            timestamp=True
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handlers
    # General application log
    app_log = log_dir / 'app.log'
    app_handler = logging.FileHandler(app_log, mode='a')
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    logger.addHandler(app_handler)
    
    # Error-only log
    error_log = log_dir / 'errors.log'
    error_handler = logging.FileHandler(error_log, mode='a')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Request/Access log (for uvicorn)
    access_log = log_dir / 'access.log'
    access_handler = logging.FileHandler(access_log, mode='a')
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(formatter)
    
    # Configure uvicorn access logger
    access_logger = logging.getLogger('uvicorn.access')
    access_logger.addHandler(access_handler)
    
    _logging_configured = True
    logging.info(f"Logging initialized - Level: {log_level}, Format: {log_format}")


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for a module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    # Ensure logging is setup before returning logger
    if not _logging_configured:
        setup_logging()
    
    return logging.getLogger(name)


def configure_uvicorn_logging() -> None:
    """
    Configure uvicorn and FastAPI logging.
    Called from main.py before starting the application.
    """
    setup_logging()


# Alias for backward compatibility
setup_logger = get_logger
