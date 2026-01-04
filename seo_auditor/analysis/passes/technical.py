"""Technical analysis pass."""
import pandas as pd
from .base import BaseAnalysisPass
from ...models.enums import AnalysisPassType

class TechnicalAnalyzer(BaseAnalysisPass):
    PASS_TYPE = AnalysisPassType.TECHNICAL
    PROMPT_FILE = "technical.md"
    
    def _get_default_prompt(self) -> str:
        return "Analyze technical SEO issues. Output JSON with issues array."
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = ["url", "status_code", "indexability", "crawl_depth", "internal_links_in", "clicks", "impressions"]
        return df[[c for c in cols if c in df.columns]].copy()
