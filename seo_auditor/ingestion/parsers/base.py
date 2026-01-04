"""Base parser class."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import pandas as pd

class BaseParser(ABC):
    EXPECTED_COLUMNS: list[str] = []
    EXPORT_NAME: str = ""
    
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
    
    def parse(self, file_path: Path) -> pd.DataFrame:
        if not file_path.exists():
            return pd.DataFrame()
        try:
            df = pd.read_csv(file_path, encoding="utf-8", low_memory=False, on_bad_lines="skip")
            df.columns = df.columns.str.strip()
            df = self.transform(df)
            self.data = df
            return df
        except Exception:
            return pd.DataFrame()
    
    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        pass
