"""Data chunking for large datasets."""
from dataclasses import dataclass
from typing import Iterator, Any
import json
import pandas as pd

@dataclass
class DataChunk:
    chunk_id: int
    total_chunks: int
    total_urls: int
    stats: dict[str, Any]
    urls: list[dict]
    issue_samples: dict[str, list[dict]]
    
    def to_prompt_context(self) -> str:
        parts = [f"## Data Chunk {self.chunk_id}/{self.total_chunks}",
                 f"Total URLs: {self.total_urls}", "", "### Statistics",
                 "```json", json.dumps(self.stats, indent=2), "```"]
        if self.issue_samples:
            parts.append("### Issue Samples")
            for name, samples in self.issue_samples.items():
                if samples:
                    parts.extend([f"#### {name}", "```json", json.dumps(samples[:10], indent=2), "```"])
        return "\n".join(parts)

class DataChunker:
    def __init__(self, max_urls: int = 500):
        self.max_urls = max_urls
    
    def chunk_for_analysis(self, df: pd.DataFrame, analysis_type: str = "general") -> Iterator[DataChunk]:
        stats = self._calc_stats(df)
        samples = self._get_samples(df)
        yield DataChunk(1, 1, len(df), stats, [], samples)
    
    def _calc_stats(self, df: pd.DataFrame) -> dict:
        stats = {"total_urls": len(df)}
        if "status_code" in df.columns:
            stats["status_codes"] = df["status_code"].value_counts().to_dict()
        if "clicks" in df.columns:
            stats["total_clicks"] = int(df["clicks"].sum())
        return stats
    
    def _get_samples(self, df: pd.DataFrame) -> dict[str, list[dict]]:
        samples = {}
        cols = ["url", "status_code", "title", "h1", "word_count", "clicks"]
        available = [c for c in cols if c in df.columns]
        
        if "title" in df.columns:
            missing = df[df["title"].isna() | (df["title"] == "")]
            samples["missing_title"] = missing[available].head(10).to_dict("records")
        if "word_count" in df.columns:
            thin = df[df["word_count"] < 300]
            samples["thin_content"] = thin[available].head(10).to_dict("records")
        return samples
