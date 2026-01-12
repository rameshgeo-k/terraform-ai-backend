#!/usr/bin/env python3
"""
Test script for the new logging configuration
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.logging_utils import get_logger, setup_logging

# Setup logging first
setup_logging()

# Get loggers for different modules
logger = get_logger(__name__)
service_logger = get_logger("app.services.chat_service")
api_logger = get_logger("app.api.routes")

def test_logging():
    """Test different log levels and loggers"""
    print("=" * 60)
    print("Testing InfraPilot Logging Configuration")
    print("=" * 60)
    
    # Test different log levels
    logger.debug("This is a DEBUG message")
    logger.info("✅ This is an INFO message")
    logger.warning("⚠️  This is a WARNING message")
    logger.error("❌ This is an ERROR message")
    
    # Test different module loggers
    service_logger.info("Chat service logger test")
    api_logger.info("API routes logger test")
    
    # Test with context
    logger.info("Processing request", extra={
        'user_id': 123,
        'request_id': 'abc-123',
        'action': 'chat_message'
    })
    
    # Test error with exception
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        logger.error("Caught exception", exc_info=True)
    
    print("=" * 60)
    print("✅ Logging test complete!")
    print("=" * 60)
    print("\nCheck the following locations:")
    print("  - Console output (above)")
    print("  - logs/app.log (all logs)")
    print("  - logs/errors.log (errors only)")
    print("  - logs/access.log (uvicorn access logs when server runs)")
    print("\nTo enable JSON logging:")
    print("  Set LOG_FORMAT=json in .env file")
    print("=" * 60)

if __name__ == "__main__":
    test_logging()
