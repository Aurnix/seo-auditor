"""Synthesize all analyses into report."""
import json
import uuid
from datetime import datetime
from typing import Optional
import pandas as pd
from ..clients.claude_client import ClaudeClient
from ..models.analysis import AnalysisPassResult, SEOIssue, ActionItem
from ..models.report import AuditReport, HealthScore, ExecutiveSummary, IssuesByCategory, ChartData
from ..models.crawl import CrawlSummary
from ..models.enums import Priority

SYSTEM_PROMPT = """Synthesize SEO analysis into a report. Output JSON:
{"health_score": {"overall": 72, "technical": 80, "content": 65, "links": 75, "explanation": "..."},
 "executive_summary": {"headline": "...", "key_findings": [], "quick_wins": [], "strategic_recommendations": [], "overall_assessment": "..."},
 "action_plan": [{"rank": 1, "title": "...", "description": "...", "priority": "high", "effort": "quick_win", "category": "technical"}]}"""

class Synthesizer:
    def __init__(self, claude_client: ClaudeClient):
        self.claude = claude_client
    
    async def synthesize(self, analyses: dict[str, AnalysisPassResult], crawl_data: pd.DataFrame, site_url: str = "") -> AuditReport:
        all_issues = [i for r in analyses.values() for i in r.issues]
        all_issues.sort(key=lambda x: x.impact_score, reverse=True)
        
        prompt = f"Site stats: {len(crawl_data)} URLs\n"
        for name, result in analyses.items():
            prompt += f"{name}: {len(result.issues)} issues - {result.summary}\n"
        prompt += "Synthesize into report JSON."
        
        result = await self.claude.analyze(SYSTEM_PROMPT, prompt)
        synthesis = self._parse(result.content)
        
        hs = synthesis.get("health_score", {})
        es = synthesis.get("executive_summary", {})
        
        issues_by_cat = IssuesByCategory()
        for issue in all_issues:
            cat = issue.category.value if hasattr(issue.category, "value") else str(issue.category)
            if hasattr(issues_by_cat, cat):
                getattr(issues_by_cat, cat).append(issue)
        
        actions = []
        for i, a in enumerate(synthesis.get("action_plan", [])):
            actions.append(ActionItem(rank=a.get("rank", i+1), title=a.get("title", "Action"),
                                       description=a.get("description", ""), priority=a.get("priority", "medium"),
                                       effort=a.get("effort", "moderate"), category=a.get("category", "technical")))
        
        return AuditReport(
            report_id=str(uuid.uuid4())[:8], site_url=site_url,
            health_score=HealthScore(overall=hs.get("overall", 50), technical=hs.get("technical", 50),
                                      content=hs.get("content", 50), links=hs.get("links", 50),
                                      explanation=hs.get("explanation", "")),
            executive_summary=ExecutiveSummary(headline=es.get("headline", "Audit Complete"),
                                                key_findings=es.get("key_findings", []),
                                                quick_wins=es.get("quick_wins", []),
                                                strategic_recommendations=es.get("strategic_recommendations", []),
                                                overall_assessment=es.get("overall_assessment", "")),
            crawl_summary=CrawlSummary(total_urls=len(crawl_data)), crawl_date=datetime.now(),
            issues=issues_by_cat, all_issues=all_issues, action_plan=actions,
            chart_data=self._build_charts(crawl_data, all_issues),
            total_tokens_used=sum(r.input_tokens + r.output_tokens for r in analyses.values()),
            has_gsc_data="clicks" in crawl_data.columns)
    
    def _parse(self, content: str) -> dict:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except: return {}
    
    def _build_charts(self, df: pd.DataFrame, issues: list) -> ChartData:
        data = ChartData()
        if "status_code" in df.columns:
            data.status_codes = {str(k): int(v) for k, v in df["status_code"].value_counts().items()}
        if "indexability" in df.columns:
            data.indexability = {str(k): int(v) for k, v in df["indexability"].value_counts().items()}
        cat_counts = {}
        for i in issues:
            c = i.category.value if hasattr(i.category, "value") else str(i.category)
            cat_counts[c] = cat_counts.get(c, 0) + 1
        data.issues_by_category = cat_counts
        return data
