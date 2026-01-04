"""Links analysis pass."""
import pandas as pd
from .base import BaseAnalysisPass
from ...models.enums import AnalysisPassType

class LinksAnalyzer(BaseAnalysisPass):
    PASS_TYPE = AnalysisPassType.LINKS
    PROMPT_FILE = "links.md"
    
    def _get_default_prompt(self) -> str:
        return "Analyze internal linking issues. Output JSON with issues array."
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = ["url", "crawl_depth", "internal_links_in", "internal_links_out", "status_code", "clicks"]
        return df[[c for c in cols if c in df.columns]].copy()
