"""Data models for crawl data."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

class PageData(BaseModel):
    url: str
    url_normalized: str = ""
    status_code: int = 0
    content_type: str = ""
    indexability: str = "indexable"
    title: Optional[str] = None
    title_length: int = 0
    meta_description: Optional[str] = None
    meta_description_length: int = 0
    h1: Optional[str] = None
    h1_count: int = 0
    word_count: int = 0
    crawl_depth: int = 0
    internal_links_in: int = 0
    internal_links_out: int = 0
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    avg_position: float = 0.0
    priority_score: float = 0.0
    model_config = {"extra": "allow"}

class CrawlSummary(BaseModel):
    total_urls: int = 0
    status_2xx: int = 0
    status_3xx: int = 0
    status_4xx: int = 0
    status_5xx: int = 0
    missing_title: int = 0
    missing_h1: int = 0
    thin_content_pages: int = 0
    total_clicks: int = 0
    total_impressions: int = 0

class CrawlData(BaseModel):
    site_url: str
    crawl_date: datetime = Field(default_factory=datetime.now)
    pages: list[PageData] = Field(default_factory=list)
    summary: CrawlSummary = Field(default_factory=CrawlSummary)
