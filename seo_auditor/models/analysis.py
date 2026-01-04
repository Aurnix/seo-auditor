"""Data models for analysis results."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from .enums import Priority, Effort, IssueCategory, AnalysisPassType

class AffectedURL(BaseModel):
    url: str
    details: dict[str, Any] = Field(default_factory=dict)
    clicks: int = 0
    impressions: int = 0

class SEOIssue(BaseModel):
    id: str
    category: IssueCategory
    title: str
    description: str
    impact: str
    priority: Priority
    effort: Effort
    affected_urls: list[AffectedURL] = Field(default_factory=list)
    affected_count: int = 0
    recommendation: str
    implementation_steps: list[str] = Field(default_factory=list)
    total_affected_clicks: int = 0
    total_affected_impressions: int = 0
    model_config = {"extra": "allow"}
    
    @property
    def impact_score(self) -> float:
        weights = {Priority.CRITICAL: 4, Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}
        return weights.get(self.priority, 2) * (1 + min(self.total_affected_clicks / 100, 2.0))

class AnalysisPassResult(BaseModel):
    pass_type: AnalysisPassType
    timestamp: datetime = Field(default_factory=datetime.now)
    issues: list[SEOIssue] = Field(default_factory=list)
    summary: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    raw_response: Optional[str] = None

class ActionItem(BaseModel):
    rank: int
    title: str
    description: str
    issues_addressed: list[str] = Field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    effort: Effort = Effort.MODERATE
    estimated_impact: str = ""
    affected_urls_count: int = 0
    category: IssueCategory = IssueCategory.TECHNICAL
    key_urls: list[str] = Field(default_factory=list)
    model_config = {"extra": "allow"}
