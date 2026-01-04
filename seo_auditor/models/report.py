"""Data models for audit report."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .crawl import CrawlSummary
from .analysis import SEOIssue, ActionItem, AnalysisPassResult
from .enums import Priority

class HealthScore(BaseModel):
    overall: int = Field(..., ge=0, le=100)
    technical: int = 100
    content: int = 100
    links: int = 100
    explanation: str = ""

class ExecutiveSummary(BaseModel):
    headline: str
    key_findings: list[str] = Field(default_factory=list)
    quick_wins: list[str] = Field(default_factory=list)
    strategic_recommendations: list[str] = Field(default_factory=list)
    overall_assessment: str = ""

class IssuesByCategory(BaseModel):
    technical: list[SEOIssue] = Field(default_factory=list)
    content: list[SEOIssue] = Field(default_factory=list)
    links: list[SEOIssue] = Field(default_factory=list)
    images: list[SEOIssue] = Field(default_factory=list)
    performance: list[SEOIssue] = Field(default_factory=list)
    
    @property
    def total_count(self) -> int:
        return sum(len(getattr(self, cat)) for cat in ["technical", "content", "links", "images", "performance"])

class ChartData(BaseModel):
    status_codes: dict[str, int] = Field(default_factory=dict)
    indexability: dict[str, int] = Field(default_factory=dict)
    issues_by_category: dict[str, int] = Field(default_factory=dict)
    issues_by_priority: dict[str, int] = Field(default_factory=dict)
    crawl_depth: dict[int, int] = Field(default_factory=dict)

class AuditReport(BaseModel):
    report_id: str
    site_url: str
    generated_at: datetime = Field(default_factory=datetime.now)
    health_score: HealthScore
    executive_summary: ExecutiveSummary
    crawl_summary: CrawlSummary
    crawl_date: datetime
    issues: IssuesByCategory
    all_issues: list[SEOIssue] = Field(default_factory=list)
    action_plan: list[ActionItem] = Field(default_factory=list)
    chart_data: ChartData = Field(default_factory=ChartData)
    analysis_passes: list[AnalysisPassResult] = Field(default_factory=list)
    total_tokens_used: int = 0
    has_gsc_data: bool = False
