"""Structured logging configuration."""
import logging
import sys
from pathlib import Path
from typing import Optional
import structlog


def setup_logging(level: str = "INFO", log_format: str = "console", log_file: Optional[Path] = None) -> None:
    """Configure structured logging."""
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=getattr(logging, level.upper()))
    for name in ["httpx", "httpcore", "anthropic", "google"]:
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str):
    """Get a logger instance."""
    return structlog.get_logger(name)
