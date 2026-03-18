"""
Professional logging configuration module for debugging and production use.

This module provides a centralized logging configuration with:
- Console and file handlers
- Rotating file handlers to manage log file sizes
- Configurable log levels
- Structured logging format with timestamps, levels, and module names
- Support for different log files per module
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


class LoggerConfig:
    """Configuration class for application logging"""
    
    # Default log directory
    LOG_DIR = Path("logs")
    
    # Default log file names
    DEFAULT_LOG_FILE = "application.log"
    ERROR_LOG_FILE = "error.log"
    
    # Log format
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # Console format (simpler for readability)
    CONSOLE_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    
    # File rotation settings
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5  # Keep 5 backup files
    
    # Default log level
    DEFAULT_LEVEL = logging.INFO


def setup_logger(
    name: str,
    level: Optional[int] = None,
    log_file: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    Set up and configure a logger with console and file handlers.
    
    Args:
        name: Logger name (typically __name__ of the module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Custom log file name (optional)
        console_output: Whether to output to console
        file_output: Whether to output to file
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
        >>> logger.debug("Debug information")
        >>> logger.error("An error occurred", exc_info=True)
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level
    if level is None:
        level = LoggerConfig.DEFAULT_LEVEL
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(
        LoggerConfig.LOG_FORMAT,
        datefmt=LoggerConfig.DATE_FORMAT
    )
    console_formatter = logging.Formatter(
        LoggerConfig.CONSOLE_FORMAT,
        datefmt=LoggerConfig.DATE_FORMAT
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output:
        # Create logs directory if it doesn't exist
        LoggerConfig.LOG_DIR.mkdir(exist_ok=True)
        
        # Determine log file path
        if log_file is None:
            log_file = LoggerConfig.DEFAULT_LOG_FILE
        log_path = LoggerConfig.LOG_DIR / log_file
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=LoggerConfig.MAX_BYTES,
            backupCount=LoggerConfig.BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Separate error log file
        error_log_path = LoggerConfig.LOG_DIR / LoggerConfig.ERROR_LOG_FILE
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path,
            maxBytes=LoggerConfig.MAX_BYTES,
            backupCount=LoggerConfig.BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get or create a logger with the given name.
    
    This is a convenience function that provides consistent logger configuration
    across the application.
    
    Args:
        name: Logger name (typically __name__ of the module)
        level: Optional logging level override
        
    Returns:
        Configured logger instance
        
    Example:
        >>> from src.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return setup_logger(name, level=level)


def set_log_level(level: int):
    """
    Set the global log level for all loggers.
    
    Args:
        level: Logging level (logging.DEBUG, logging.INFO, etc.)
        
    Example:
        >>> import logging
        >>> from src.utils.logger import set_log_level
        >>> set_log_level(logging.DEBUG)  # Enable debug logging
    """
    LoggerConfig.DEFAULT_LEVEL = level
    logging.getLogger().setLevel(level)


def log_function_call(logger: logging.Logger):
    """
    Decorator to log function calls with arguments and return values.
    
    Args:
        logger: Logger instance to use
        
    Example:
        >>> logger = get_logger(__name__)
        >>> @log_function_call(logger)
        >>> def process_data(data):
        >>>     return data * 2
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} returned: {result}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} raised {type(e).__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator


# Create a default application logger
app_logger = get_logger("ntt_capstone_app")


def log_startup_info():
    """Log application startup information"""
    app_logger.info("="*80)
    app_logger.info("Application Starting")
    app_logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    app_logger.info(f"Log Directory: {LoggerConfig.LOG_DIR.absolute()}")
    app_logger.info(f"Log Level: {logging.getLevelName(LoggerConfig.DEFAULT_LEVEL)}")
    app_logger.info("="*80)


def log_shutdown_info():
    """Log application shutdown information"""
    app_logger.info("="*80)
    app_logger.info("Application Shutting Down")
    app_logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    app_logger.info("="*80)


# Log startup when module is imported
if __name__ != "__main__":
    log_startup_info()
