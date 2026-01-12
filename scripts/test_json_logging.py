#!/usr/bin/env python3
"""
Test JSON logging format
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Override settings to use JSON format
os.environ['LOG_FORMAT'] = 'json'

from app.utils.logging_utils import get_logger, setup_logging

# Setup logging with JSON format
setup_logging()

logger = get_logger(__name__)

def test_json_logging():
    """Test JSON formatted logging"""
    print("=" * 60)
    print("Testing JSON Logging Format")
    print("=" * 60)
    
    logger.info("User login", extra={'user_id': 123, 'username': 'john.doe'})
    logger.info("API request", extra={
        'method': 'POST',
        'endpoint': '/api/chat',
        'status_code': 200,
        'duration_ms': 250
    })
    logger.warning("Rate limit approaching", extra={
        'user_id': 456,
        'requests_count': 95,
        'limit': 100
    })
    logger.error("Database connection failed", extra={
        'host': 'localhost',
        'port': 5432,
        'database': 'infrapilot'
    })
    
    print("=" * 60)
    print("✅ JSON logging test complete!")
    print("Check logs/app.log for JSON formatted output")
    print("=" * 60)

if __name__ == "__main__":
    test_json_logging()
