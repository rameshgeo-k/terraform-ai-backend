"""
Logging Configuration
Structured logging setup with JSON formatter
"""

import logging
from pathlib import Path
from pythonjsonlogger import jsonlogger
from app.core.config import settings


def setup_logging() -> None:
    """Setup application logging"""
    log_config = settings.logging
    log_dir = Path(log_config.directory)
    log_level = log_config.level.upper()
    log_format = log_config.format
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    
    if log_format == 'json':
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            timestamp=True
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handlers
    request_log = log_dir / 'requests.log'
    request_handler = logging.FileHandler(request_log)
    request_handler.setLevel(logging.INFO)
    request_handler.setFormatter(formatter)
    
    error_log = log_dir / 'errors.log'
    error_handler = logging.FileHandler(error_log)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    logger.addHandler(request_handler)
    logger.addHandler(error_handler)
    
    logging.info("Logging initialized")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)
