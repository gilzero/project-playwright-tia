# app/logger.py
import os
import logging
import logging.handlers
from typing import Dict, Optional, Any
from datetime import datetime

# Constants for logging configuration
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_LEVEL = "INFO"
MAX_LOG_SIZE_MB = 10 * 1024 * 1024  # 10MB in bytes
BACKUP_COUNT = 5  # Number of backup files to keep
LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Global logger instance
_logger = None

def get_logger(name: str = 'techinasia_scraper') -> logging.Logger:
    """
    Get the global logger instance. If it hasn't been initialized, initialize it.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        _logger = setup_logging(name=name)
    return _logger

def setup_logging(
    name: str = 'techinasia_scraper',
    log_dir: str = DEFAULT_LOG_DIR,
    log_level: str = DEFAULT_LOG_LEVEL,
    max_size: int = MAX_LOG_SIZE_MB,
    backup_count: int = BACKUP_COUNT
) -> logging.Logger:
    """
    Set up logging configuration with separate log files for different log levels and proper rotation.
    
    Args:
        name: Logger name
        log_dir: Directory to store log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_size: Maximum size of each log file in bytes before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Logger instance
    """
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Create handlers for different log levels with rotation
    handlers = {
        'debug': create_rotating_handler(
            os.path.join(log_dir, 'debug.log'),
            level=logging.DEBUG,
            formatter=formatter,
            max_bytes=max_size,
            backup_count=backup_count
        ),
        'info': create_rotating_handler(
            os.path.join(log_dir, 'info.log'),
            level=logging.INFO,
            formatter=formatter,
            max_bytes=max_size,
            backup_count=backup_count
        ),
        'error': create_rotating_handler(
            os.path.join(log_dir, 'error.log'),
            level=logging.ERROR,
            formatter=formatter,
            max_bytes=max_size,
            backup_count=backup_count
        ),
        'console': logging.StreamHandler()
    }
    
    # Set formatter for console handler
    handlers['console'].setFormatter(formatter)
    handlers['console'].setLevel(numeric_level)
    
    # Add all handlers to logger
    for handler in handlers.values():
        logger.addHandler(handler)
    
    # Log initialization
    logger.info(f"Logging initialized at level {log_level}")
    logger.info(f"Log files will be stored in {os.path.abspath(log_dir)}")
    logger.info(f"Log rotation: {backup_count} files, {max_size/1024/1024:.1f}MB each")
    
    return logger

def create_rotating_handler(
    filename: str,
    level: int,
    formatter: logging.Formatter,
    max_bytes: int,
    backup_count: int
) -> logging.handlers.RotatingFileHandler:
    """
    Create a rotating file handler for a specific log level.
    
    Args:
        filename: Path to the log file
        level: Logging level
        formatter: Log formatter
        max_bytes: Maximum size of the log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        RotatingFileHandler instance
    """
    handler = logging.handlers.RotatingFileHandler(
        filename,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    
    # Add a filter to only include records at the specified level or higher
    # but exclude records that would go to a more severe log file
    if level == logging.DEBUG:
        handler.addFilter(lambda record: record.levelno < logging.INFO)
    elif level == logging.INFO:
        handler.addFilter(lambda record: logging.INFO <= record.levelno < logging.ERROR)
    
    return handler

def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An error occurred",
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an exception with context information.
    
    Args:
        logger: Logger instance
        exception: Exception to log
        message: Custom message to include
        context: Additional context information
    """
    error_details = {
        'exception_type': type(exception).__name__,
        'exception_message': str(exception),
        'context': context or {}
    }
    
    logger.error(f"{message}: {error_details}", exc_info=True)

def log_summary(
    total_articles: int,
    processed_ids: set,
    incomplete_articles: int,
    start_time: datetime,
    end_time: datetime,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log summary statistics of the scraping process.
    
    Args:
        total_articles: Total number of articles found
        processed_ids: Set of processed article IDs
        incomplete_articles: Number of incomplete articles skipped
        start_time: Start time of the scraping process
        end_time: End time of the scraping process
        config: Configuration used for scraping (optional)
    """
    logger = get_logger()
    duration = end_time - start_time
    duration_seconds = duration.total_seconds()
    articles_per_second = len(processed_ids) / duration_seconds if duration_seconds > 0 else 0
    
    logger.info("📊 --- Scraping Summary ---")
    logger.info(f"📰 Total articles found: {total_articles}")
    logger.info(f"✅ Valid articles scraped: {len(processed_ids)}")
    logger.info(f"⚠️ Incomplete articles skipped: {incomplete_articles}")
    logger.info(f"🔄 Duplicate articles skipped: {total_articles - len(processed_ids) - incomplete_articles}")
    logger.info(f"⏱️ Scraping duration: {duration} ({duration_seconds:.2f} seconds)")
    logger.info(f"⚡ Performance: {articles_per_second:.2f} articles/second")
    
    if config:
        logger.info("⚙️ --- Configuration ---")
        for key, value in config.items():
            logger.info(f"  {key}: {value}") 