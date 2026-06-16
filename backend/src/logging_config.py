"""
Structured logging configuration using structlog with JSON output.
Logs include: timestamp, user_id, event, status, latency_ms, error
"""
import logging
import sys
import structlog


def setup_logging():
    """
    Configure structlog for structured JSON logging.
    
    Features:
    - JSON formatted output to stdout
    - ISO 8601 timestamps
    - Contextual user_id binding
    - Request latency tracking
    - Exception formatting
    """
    # Configure standard Python logging as the base layer
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Configure structlog with comprehensive processors
    structlog.configure(
        processors=[
            # Merge context variables (user_id, request_id, etc.)
            structlog.contextvars.merge_contextvars,
            
            # Add log level and logger name
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            
            # Add ISO 8601 timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            
            # Render stack traces and exceptions
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            
            # Final JSON renderer
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger():
    """Get a structlog logger instance."""
    return structlog.get_logger()
