"""Base parser class."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)


class BaseParser(ABC):
    """Base class for Screaming Frog export parsers."""

    EXPECTED_COLUMNS: list[str] = []
    EXPORT_NAME: str = ""

    def __init__(self):
        self.data: Optional[pd.DataFrame] = None

    def parse(self, file_path: Path) -> pd.DataFrame:
        """Parse a CSV export file.

        Args:
            file_path: Path to the CSV file

        Returns:
            DataFrame with parsed and transformed data, or empty DataFrame on error
        """
        if not file_path.exists():
            logger.warning("Parser file not found", path=str(file_path), parser=self.EXPORT_NAME)
            return pd.DataFrame()

        try:
            df = pd.read_csv(
                file_path, encoding="utf-8", low_memory=False, on_bad_lines="skip"
            )
            df.columns = df.columns.str.strip()
            df = self.transform(df)
            self.data = df
            logger.info(
                "Parsed export file",
                path=str(file_path),
                parser=self.EXPORT_NAME,
                row_count=len(df),
            )
            return df

        except pd.errors.EmptyDataError:
            logger.warning("Empty CSV file", path=str(file_path), parser=self.EXPORT_NAME)
            return pd.DataFrame()

        except pd.errors.ParserError as e:
            logger.error(
                "CSV parsing error",
                path=str(file_path),
                parser=self.EXPORT_NAME,
                error=str(e),
            )
            return pd.DataFrame()

        except UnicodeDecodeError as e:
            logger.error(
                "Encoding error reading CSV",
                path=str(file_path),
                parser=self.EXPORT_NAME,
                error=str(e),
            )
            return pd.DataFrame()

        except Exception as e:
            logger.error(
                "Unexpected error parsing file",
                path=str(file_path),
                parser=self.EXPORT_NAME,
                error_type=type(e).__name__,
                error=str(e),
            )
            return pd.DataFrame()

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the raw DataFrame. Subclasses must implement this."""
        pass
