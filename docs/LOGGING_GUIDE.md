# Logging Configuration Guide

## Overview

InfraPilot uses a modern, structured logging system that supports both **text** and **JSON** formats. This guide explains how to configure and use the logging system.

## Features

✅ **Structured Logging**: Support for text and JSON formats  
✅ **Multiple Log Files**: Separate logs for general app logs, errors, and access logs  
✅ **Console & File Output**: Logs go to both console and files  
✅ **Configurable Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL  
✅ **Context Support**: Add structured data to log messages  
✅ **Production Ready**: Optimized for log aggregation systems  

## Configuration

### Environment Variables (`.env`)

```env
# Logging Configuration
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=text         # text or json
LOG_DIRECTORY=logs      # Directory for log files
LOG_TO_FILE=True        # Enable/disable file logging
```

### Settings in Code

Configuration is managed through `app.core.config.Settings`:

```python
from app.core.config import settings

# Access logging settings
print(settings.LOG_LEVEL)      # "INFO"
print(settings.LOG_FORMAT)     # "text" or "json"
print(settings.LOG_DIRECTORY)  # "logs"
print(settings.LOG_TO_FILE)    # True or False
```

## Usage

### Basic Logging

```python
from app.utils.logging_utils import get_logger

# Get logger for current module
logger = get_logger(__name__)

# Log messages
logger.debug("Debugging information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error!")
```

### Structured Logging (with context)

```python
# Add structured data to logs
logger.info("User login", extra={
    'user_id': 123,
    'username': 'john.doe',
    'ip_address': '192.168.1.1'
})

logger.error("API call failed", extra={
    'endpoint': '/api/chat',
    'status_code': 500,
    'duration_ms': 1250,
    'error': 'Connection timeout'
})
```

### Exception Logging

```python
try:
    # Some operation
    result = risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True, extra={
        'operation': 'risky_operation',
        'user_id': 456
    })
```

### FastAPI Integration

Logging is automatically initialized when the app starts:

```python
# app/main.py
from app.utils.logging_utils import configure_uvicorn_logging

# Configure logging before creating app
configure_uvicorn_logging()

app = FastAPI(...)
```

## Log Files

When `LOG_TO_FILE=True`, the following log files are created in the `logs/` directory:

### 1. `app.log`
- **Content**: All application logs (INFO and above)
- **Use**: General application monitoring
- **Example**:
  ```
  2025-11-21 18:10:31 - app.services.chat_service - INFO - Processing chat request
  2025-11-21 18:10:32 - app.api.routes - INFO - GET /api/models - 200
  ```

### 2. `errors.log`
- **Content**: Error and critical logs only
- **Use**: Quick error detection and debugging
- **Example**:
  ```
  2025-11-21 18:15:45 - app.services.auth - ERROR - Authentication failed
  2025-11-21 18:16:12 - app.core.database - CRITICAL - Database connection lost
  ```

### 3. `access.log`
- **Content**: HTTP access logs from uvicorn
- **Use**: Request monitoring and analytics
- **Example**:
  ```
  2025-11-21 18:20:15 - uvicorn.access - INFO - 127.0.0.1:45678 - "GET /api/health HTTP/1.1" 200
  ```

## Text vs JSON Format

### Text Format (Default)

**Good for:**
- Development and debugging
- Human-readable logs
- Simple grep/tail operations

**Example:**
```
2025-11-21 18:10:31 - app.services.chat - INFO - User login
```

**Configuration:**
```env
LOG_FORMAT=text
```

### JSON Format

**Good for:**
- Production environments
- Log aggregation (ELK, Splunk, CloudWatch)
- Structured queries
- Machine parsing

**Example:**
```json
{
  "asctime": "2025-11-21 18:10:31,825",
  "name": "app.services.chat",
  "levelname": "INFO",
  "message": "User login",
  "user_id": 123,
  "username": "john.doe",
  "timestamp": "2025-11-21T12:40:31.825435+00:00"
}
```

**Configuration:**
```env
LOG_FORMAT=json
```

## Log Levels

### DEBUG
- Detailed diagnostic information
- Not logged to files in production
- Example: Variable values, function calls

### INFO (Default)
- General informational messages
- Application lifecycle events
- Example: "Server started", "Request processed"

### WARNING
- Warning messages for potentially harmful situations
- Application still works, but attention needed
- Example: "Deprecated API used", "Rate limit approaching"

### ERROR
- Error events that might still allow the app to continue
- Example: "Database query failed", "API timeout"

### CRITICAL
- Very severe errors that may cause the app to terminate
- Example: "Database unavailable", "Out of memory"

## Best Practices

### 1. Use Appropriate Log Levels

```python
# ✅ Good
logger.debug(f"Processing {len(items)} items")  # Development details
logger.info("User registered successfully")      # Important events
logger.warning("API rate limit at 90%")          # Potential issues
logger.error("Payment processing failed")        # Actual errors
logger.critical("Database connection lost")      # Severe issues

# ❌ Bad
logger.info("Variable x = 5")                    # Too detailed for INFO
logger.error("User clicked button")              # Not an error
```

### 2. Add Context with `extra`

```python
# ✅ Good - Structured context
logger.info("Order created", extra={
    'order_id': order.id,
    'customer_id': customer.id,
    'amount': order.total,
    'currency': 'USD'
})

# ❌ Bad - Unstructured string
logger.info(f"Order {order.id} created for customer {customer.id} amount ${order.total}")
```

### 3. Log Exceptions Properly

```python
# ✅ Good - Full traceback
try:
    process_payment()
except PaymentError as e:
    logger.error("Payment failed", exc_info=True, extra={
        'payment_id': payment.id,
        'error_code': e.code
    })

# ❌ Bad - No traceback
except PaymentError as e:
    logger.error(f"Payment failed: {str(e)}")
```

### 4. Use Module-Level Loggers

```python
# ✅ Good - Each module has its own logger
# app/services/chat_service.py
logger = get_logger(__name__)  # Creates 'app.services.chat_service'

# ❌ Bad - Hardcoded logger names
logger = get_logger("my_logger")
```

## Testing Logging

### Manual Testing

```bash
# Test text format
cd backend
source .venv/bin/activate
python scripts/test_logging.py

# Test JSON format
python scripts/test_json_logging.py
```

### Viewing Logs

```bash
# View all logs
tail -f logs/app.log

# View only errors
tail -f logs/errors.log

# View access logs
tail -f logs/access.log

# Search logs
grep "ERROR" logs/app.log
grep "user_id.*123" logs/app.log

# JSON logs (with jq)
tail logs/app.log | jq '.'
```

## Production Recommendations

### 1. Use JSON Format

```env
LOG_FORMAT=json
LOG_LEVEL=INFO
```

### 2. Ship Logs to Aggregation Service

**AWS CloudWatch:**
```bash
# Install CloudWatch agent
# Configure to ship logs/app.log and logs/errors.log
```

**ELK Stack:**
```bash
# Use Filebeat to ship JSON logs
# Logs are already in JSON format for Elasticsearch
```

**Splunk:**
```bash
# Configure Splunk forwarder
# JSON format works great with Splunk
```

### 3. Log Rotation

Currently using Python's built-in file handlers. For production, consider:

```bash
# Install logrotate
sudo apt-get install logrotate

# Create /etc/logrotate.d/infrapilot
/var/www/projects/infrapilot/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload infrapilot
    endscript
}
```

## Backward Compatibility

The old `setup_logger()` function still works:

```python
# Old style (still works)
from app.utils.logging_utils import setup_logger
logger = setup_logger(__name__)

# New style (recommended)
from app.utils.logging_utils import get_logger
logger = get_logger(__name__)
```

## Migration from Old System

All logging configuration is now centralized in `app.core.config.Settings`:

```python
# New (recommended)
from app.core.config import settings
log_level = settings.LOG_LEVEL
log_to_file = settings.LOG_TO_FILE
log_format = settings.LOG_FORMAT
```

## Troubleshooting

### Logs not appearing in files

```bash
# Check LOG_TO_FILE setting
grep LOG_TO_FILE backend/.env

# Check directory permissions
ls -ld backend/logs

# Create directory manually
mkdir -p backend/logs
```

### JSON logging not working

```bash
# Install python-json-logger
pip install python-json-logger

# Verify installation
python -c "from pythonjsonlogger import jsonlogger; print('OK')"
```

### Too much/little logging

```bash
# Adjust log level in .env
LOG_LEVEL=DEBUG    # More verbose
LOG_LEVEL=WARNING  # Less verbose
LOG_LEVEL=INFO     # Default
```

## Examples

### Complete Service Example

```python
# app/services/payment_service.py
from app.utils.logging_utils import get_logger
from app.core.database import get_db

logger = get_logger(__name__)

class PaymentService:
    def process_payment(self, order_id: int, amount: float):
        logger.info("Processing payment", extra={
            'order_id': order_id,
            'amount': amount,
            'service': 'payment'
        })
        
        try:
            # Process payment
            result = self._charge_card(amount)
            
            logger.info("Payment successful", extra={
                'order_id': order_id,
                'transaction_id': result.id,
                'amount': amount
            })
            
            return result
            
        except PaymentError as e:
            logger.error("Payment failed", exc_info=True, extra={
                'order_id': order_id,
                'amount': amount,
                'error_code': e.code,
                'error_message': str(e)
            })
            raise
```

---

**Modern, structured logging for InfraPilot! 📝**
