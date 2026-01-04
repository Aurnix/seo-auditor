"""Content analysis pass."""
import pandas as pd
from .base import BaseAnalysisPass
from ...models.enums import AnalysisPassType

class ContentAnalyzer(BaseAnalysisPass):
    PASS_TYPE = AnalysisPassType.CONTENT
    PROMPT_FILE = "content.md"
    
    def _get_default_prompt(self) -> str:
        return "Analyze content SEO issues. Output JSON with issues array."
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = ["url", "title", "title_length", "meta_description", "meta_description_length",
                "h1", "h1_count", "word_count", "clicks", "impressions", "ctr"]
        return df[[c for c in cols if c in df.columns]].copy()
