"""Configuration module for SEO Auditor."""
from .settings import settings
from .thresholds import thresholds, SEOThresholds
from .logging_config import setup_logging, get_logger

__all__ = ["settings", "thresholds", "SEOThresholds", "setup_logging", "get_logger"]
