# Logging Documentation

## Overview

This application uses a professional Python logging system designed for both debugging and production use. The logging system provides:

- **Centralized configuration** through `src/utils/logger.py`
- **Multiple log outputs**: Console and rotating file handlers
- **Structured logging format** with timestamps, module names, and log levels
- **Automatic log rotation** to prevent disk space issues
- **Separate error logs** for critical issues
- **Easy integration** across all modules

## Quick Start

### Basic Usage

```python
from src.utils.logger import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Log messages at different levels
logger.debug("Detailed debugging information")
logger.info("General informational messages")
logger.warning("Warning messages for potential issues")
logger.error("Error messages for failures")
logger.critical("Critical issues that need immediate attention")
```

### Logging Exceptions

```python
try:
    # Your code here
    result = process_data()
except Exception as e:
    # Log with full stack trace
    logger.error(f"Failed to process data: {str(e)}", exc_info=True)
    raise
```

## Log Levels

| Level | Value | Usage |
|-------|-------|-------|
| DEBUG | 10 | Detailed information for diagnosing problems |
| INFO | 20 | Confirmation that things are working as expected |
| WARNING | 30 | Indication that something unexpected happened |
| ERROR | 40 | Serious problem that prevented a function from completing |
| CRITICAL | 50 | Very serious error that may cause the application to stop |

## Log Files

All log files are stored in the `logs/` directory (created automatically):

### Main Log Files

- **`logs/application.log`**: All log messages (INFO and above by default)
- **`logs/error.log`**: Only ERROR and CRITICAL messages

### Log Rotation

- **Max file size**: 10 MB per log file
- **Backup count**: 5 backup files kept
- **Naming convention**: `application.log.1`, `application.log.2`, etc.

When a log file reaches 10 MB, it's automatically rotated:
- `application.log` → `application.log.1`
- `application.log.1` → `application.log.2`
- ... and so on

## Log Format

### File Log Format

```
<timestamp> - <module_name> - <level> - <function>:<line_number> - <message>
```

**Example:**
```
2026-03-15 01:30:45 - src.graph_builder.job_match_graph - INFO - run:75 - Running job matching workflow with 3 resume(s)
```

### Console Log Format (Simplified)

```
<timestamp> - <level> - <module_name> - <message>
```

**Example:**
```
2026-03-15 01:30:45 - INFO - src.graph_builder.job_match_graph - Running job matching workflow with 3 resume(s)
```

## Configuration

### Default Settings

Located in `src/utils/logger.py`:

```python
class LoggerConfig:
    LOG_DIR = Path("logs")
    DEFAULT_LOG_FILE = "application.log"
    ERROR_LOG_FILE = "error.log"
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5
    DEFAULT_LEVEL = logging.INFO
```

### Changing Log Level

#### For All Loggers (Application-wide)

```python
import logging
from src.utils.logger import set_log_level

# Enable debug logging globally
set_log_level(logging.DEBUG)
```

#### For a Specific Module

```python
import logging
from src.utils.logger import get_logger

# Create logger with DEBUG level for this module only
logger = get_logger(__name__, level=logging.DEBUG)
```

### Creating Module-Specific Log Files

```python
from src.utils.logger import setup_logger

# Create logger that writes to a specific file
logger = setup_logger(
    name=__name__,
    log_file="my_module.log",  # Custom log file
    level=logging.DEBUG
)
```

## Advanced Features

### Function Call Logging Decorator

Automatically log function calls, arguments, and return values:

```python
from src.utils.logger import get_logger, log_function_call

logger = get_logger(__name__)

@log_function_call(logger)
def process_data(data, mode="default"):
    # Your function code
    return processed_result
```

This will log:
```
DEBUG - Calling process_data with args=('data_value',), kwargs={'mode': 'default'}
DEBUG - process_data returned: processed_result
```

### Startup and Shutdown Logging

```python
from src.utils.logger import log_startup_info, log_shutdown_info

# Log application startup
log_startup_info()

# Your application code here

# Log application shutdown
log_shutdown_info()
```

### Disabling File or Console Output

```python
from src.utils.logger import setup_logger

# Console output only (no file logging)
logger = setup_logger(
    name=__name__,
    file_output=False,
    console_output=True
)

# File output only (no console logging)
logger = setup_logger(
    name=__name__,
    file_output=True,
    console_output=False
)
```

## Integration Examples

### In Graph Builders

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MyGraphBuilder:
    def __init__(self, llm):
        logger.info("Initializing MyGraphBuilder")
        self.llm = llm
    
    def build(self):
        logger.info("Building workflow graph")
        try:
            # Build logic here
            logger.debug("Adding nodes to graph")
            # ...
            logger.info("Workflow graph built successfully")
        except Exception as e:
            logger.error(f"Failed to build graph: {str(e)}", exc_info=True)
            raise
```

### In Node Functions

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

def process_node(state):
    logger.info("Processing node")
    try:
        logger.debug(f"Current state: {state}")
        # Processing logic
        result = do_processing(state)
        logger.info("Node processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Node processing failed: {str(e)}", exc_info=True)
        raise
```

### In API Endpoints or Streamlit Apps

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)

def handle_request(data):
    logger.info(f"Received request with {len(data)} items")
    try:
        result = process_request(data)
        logger.info("Request processed successfully")
        return result
    except Exception as e:
        logger.error(f"Request processing failed: {str(e)}", exc_info=True)
        return {"error": str(e)}
```

## Best Practices

### 1. Use Appropriate Log Levels

- **DEBUG**: Detailed diagnostic information (variable values, function flow)
- **INFO**: Major events (workflow started, completed, key milestones)
- **WARNING**: Unexpected but recoverable issues
- **ERROR**: Errors that prevent a function from completing
- **CRITICAL**: Application-level failures

### 2. Log at Entry and Exit Points

```python
def important_function(data):
    logger.info(f"Starting important_function with {len(data)} items")
    try:
        result = process(data)
        logger.info("important_function completed successfully")
        return result
    except Exception as e:
        logger.error(f"important_function failed: {str(e)}", exc_info=True)
        raise
```

### 3. Include Context in Log Messages

```python
# Good: Provides context
logger.info(f"Processing {candidate_name} for job {job_id}")

# Bad: Lacks context
logger.info("Processing started")
```

### 4. Use exc_info=True for Exceptions

```python
try:
    risky_operation()
except Exception as e:
    # Include full stack trace
    logger.error(f"Operation failed: {str(e)}", exc_info=True)
```

### 5. Don't Log Sensitive Information

```python
# Bad: Logs sensitive data
logger.info(f"User credentials: {username}:{password}")

# Good: Logs safely
logger.info(f"User {username} authenticated successfully")
```

### 6. Use String Formatting for Performance

```python
# Good: Lazy evaluation
logger.debug("Processing item: %s", large_object)

# Also good: f-string (evaluated immediately)
logger.info(f"Processed {count} items")
```

## Troubleshooting

### Logs Not Appearing

1. Check log level settings
2. Verify `logs/` directory exists and is writable
3. Check if handlers are properly attached to logger

### Too Many Log Files

Adjust rotation settings in `src/utils/logger.py`:

```python
MAX_BYTES = 5 * 1024 * 1024  # Reduce to 5 MB
BACKUP_COUNT = 3  # Keep fewer backups
```

### Performance Issues

- Reduce log level in production (use INFO instead of DEBUG)
- Disable console output for high-throughput scenarios
- Use lazy evaluation for expensive string operations

### Log File Permissions

Ensure the application has write permissions to the `logs/` directory:

```bash
# Linux/Mac
chmod 755 logs/

# Windows
icacls logs /grant Users:F
```

## Viewing Logs

### Real-time Monitoring (Linux/Mac)

```bash
# Watch main log
tail -f logs/application.log

# Watch error log
tail -f logs/error.log

# Search for specific patterns
grep "ERROR" logs/application.log
```

### Real-time Monitoring (Windows)

```powershell
# PowerShell
Get-Content logs\application.log -Wait -Tail 50

# Command Prompt
powershell Get-Content logs\application.log -Wait
```

### Log Analysis

```bash
# Count errors
grep -c "ERROR" logs/application.log

# Find all warnings
grep "WARNING" logs/application.log

# Show logs from specific module
grep "job_match_graph" logs/application.log
```

## Environment-Specific Configuration

### Development

```python
import logging
from src.utils.logger import set_log_level

if os.getenv("ENVIRONMENT") == "development":
    set_log_level(logging.DEBUG)
```

### Production

```python
import logging
from src.utils.logger import set_log_level

if os.getenv("ENVIRONMENT") == "production":
    set_log_level(logging.INFO)
```

### Testing

```python
import logging
from src.utils.logger import setup_logger

# Disable logging during tests
logger = setup_logger(
    __name__,
    level=logging.CRITICAL,
    file_output=False,
    console_output=False
)
```

## Summary

The logging system provides comprehensive debugging and monitoring capabilities:

✅ **Centralized configuration** - Easy to manage and consistent across modules  
✅ **Automatic log rotation** - Prevents disk space issues  
✅ **Multiple outputs** - Console for development, files for production  
✅ **Structured format** - Easy to parse and analyze  
✅ **Exception tracking** - Full stack traces when needed  
✅ **Flexible levels** - From DEBUG to CRITICAL  
✅ **Production-ready** - Suitable for professional applications  

For questions or issues, refer to `src/utils/logger.py` for implementation details.
