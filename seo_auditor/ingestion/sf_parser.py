"""Main SF parser orchestrator."""
from pathlib import Path
import pandas as pd
from ..utils.url import normalize_url
from .parsers.internal_html import InternalHTMLParser

class SFParser:
    def __init__(self):
        self.internal_html = InternalHTMLParser()
    
    def parse_export(self, export_dir: Path) -> pd.DataFrame:
        file_map = {
            "internal_html.csv": self.internal_html,
            "internal_all.csv": self.internal_html,
        }
        
        for filename, parser in file_map.items():
            path = export_dir / filename
            if path.exists():
                parser.parse(path)
                break
        
        if self.internal_html.data is None:
            return pd.DataFrame()
        
        df = self.internal_html.data.copy()
        df["url_normalized"] = df["url"].apply(normalize_url)
        return df
