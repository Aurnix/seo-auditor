"""Internal HTML parser."""
import pandas as pd
from .base import BaseParser

class InternalHTMLParser(BaseParser):
    EXPORT_NAME = "internal_html"
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = {
            "Address": "url", "Status Code": "status_code", "Content Type": "content_type",
            "Indexability": "indexability", "Title 1": "title", "Title 1 Length": "title_length",
            "Meta Description 1": "meta_description", "Meta Description 1 Length": "meta_description_length",
            "H1-1": "h1", "H1-1 Length": "h1_length", "Word Count": "word_count",
            "Crawl Depth": "crawl_depth", "Inlinks": "internal_links_in",
            "Outlinks": "internal_links_out", "Response Time": "response_time_ms", "Size": "size_bytes",
        }
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
        
        h1_cols = [c for c in df.columns if c.startswith("H1-") and "Length" not in c]
        df["h1_count"] = df[h1_cols].notna().sum(axis=1) if h1_cols else 0
        
        for col in ["status_code", "title_length", "meta_description_length", "word_count", "crawl_depth"]:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)
        return df
