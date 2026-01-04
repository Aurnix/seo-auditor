"""Base analysis pass."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import json
import pandas as pd
from ...clients.claude_client import ClaudeClient
from ...models.analysis import AnalysisPassResult, SEOIssue, AffectedURL
from ...models.enums import AnalysisPassType
from ..chunking import DataChunker

class BaseAnalysisPass(ABC):
    PASS_TYPE: AnalysisPassType
    PROMPT_FILE: str
    
    def __init__(self, claude_client: ClaudeClient):
        self.claude = claude_client
        self.chunker = DataChunker()
        self._system_prompt: Optional[str] = None
    
    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            path = Path(__file__).parent.parent.parent / "config" / "prompts" / self.PROMPT_FILE
            self._system_prompt = path.read_text() if path.exists() else self._get_default_prompt()
        return self._system_prompt
    
    @abstractmethod
    def _get_default_prompt(self) -> str: pass
    
    @abstractmethod
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame: pass
    
    async def analyze(self, df: pd.DataFrame) -> AnalysisPassResult:
        prepared = self._prepare_data(df)
        chunks = list(self.chunker.chunk_for_analysis(prepared, self.PASS_TYPE.value))
        
        all_issues = []
        total_in, total_out = 0, 0
        
        for chunk in chunks:
            prompt = f"Analyze this SEO data:\n{chunk.to_prompt_context()}\nProvide JSON analysis."
            result = await self.claude.analyze(self.system_prompt, prompt)
            total_in += result.input_tokens
            total_out += result.output_tokens
            parsed = self._parse_response(result.content)
            all_issues.extend(self._convert_issues(parsed.get("issues", [])))
        
        return AnalysisPassResult(pass_type=self.PASS_TYPE, issues=all_issues,
                                   summary=f"Found {len(all_issues)} issues",
                                   input_tokens=total_in, output_tokens=total_out)
    
    def _parse_response(self, content: str) -> dict:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except: return {"issues": []}
    
    def _convert_issues(self, raw: list[dict]) -> list[SEOIssue]:
        issues = []
        for r in raw:
            try:
                affected = [AffectedURL(url=u) if isinstance(u, str) else AffectedURL(**u) 
                           for u in r.get("affected_urls", [])[:50]]
                issues.append(SEOIssue(
                    id=r.get("id", f"{self.PASS_TYPE.value}_{len(issues)}"),
                    category=r.get("category", self.PASS_TYPE.value),
                    title=r.get("title", "Issue"), description=r.get("description", ""),
                    impact=r.get("impact", ""), priority=r.get("priority", "medium"),
                    effort=r.get("effort", "moderate"), affected_urls=affected,
                    affected_count=r.get("affected_count", len(affected)),
                    recommendation=r.get("recommendation", ""),
                    implementation_steps=r.get("implementation_steps", [])))
            except: pass
        return issues
