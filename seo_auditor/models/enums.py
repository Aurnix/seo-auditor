"""Shared enumerations."""
from enum import Enum

class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Effort(str, Enum):
    QUICK_WIN = "quick_win"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    PROJECT = "project"

class IssueCategory(str, Enum):
    TECHNICAL = "technical"
    CONTENT = "content"
    LINKS = "links"
    IMAGES = "images"
    PERFORMANCE = "performance"
    STRUCTURED_DATA = "structured_data"

class Indexability(str, Enum):
    INDEXABLE = "indexable"
    NON_INDEXABLE = "non_indexable"
    BLOCKED_BY_ROBOTS = "blocked_by_robots"
    BLOCKED_BY_NOINDEX = "blocked_by_noindex"

class CrawlStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class AnalysisPassType(str, Enum):
    TECHNICAL = "technical"
    CONTENT = "content"
    LINKS = "links"
    PERFORMANCE = "performance"
    SYNTHESIS = "synthesis"
