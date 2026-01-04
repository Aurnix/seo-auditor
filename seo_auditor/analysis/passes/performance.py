"""Performance analysis pass."""
import pandas as pd
from .base import BaseAnalysisPass
from ...models.enums import AnalysisPassType
from ...models.analysis import AnalysisPassResult

class PerformanceAnalyzer(BaseAnalysisPass):
    PASS_TYPE = AnalysisPassType.PERFORMANCE
    PROMPT_FILE = "performance.md"
    
    def _get_default_prompt(self) -> str:
        return "Analyze GSC performance opportunities. Output JSON."
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        if "impressions" not in df.columns:
            return pd.DataFrame()
        return df[df["impressions"] > 0].copy()
    
    async def analyze(self, df: pd.DataFrame) -> AnalysisPassResult:
        prepared = self._prepare_data(df)
        if prepared.empty:
            return AnalysisPassResult(pass_type=self.PASS_TYPE, issues=[], summary="No GSC data")
        return await super().analyze(df)
