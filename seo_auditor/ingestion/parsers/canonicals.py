"""Canonical URL parser for Screaming Frog exports."""
import pandas as pd
from .base import BaseParser


class CanonicalsParser(BaseParser):
    """Parser for canonical-related Screaming Frog exports."""

    EXPORT_NAME = "canonicals"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform canonical data to standardized format.

        Handles canonicals.csv and related exports containing:
        - Page URL
        - Canonical URL
        - Canonical link element issues
        """
        mapping = {
            "Address": "url",
            "Canonical Link Element 1": "canonical_url",
            "Canonical Link Element 1 Status": "canonical_status",
            "Canonical Link Element": "canonical_url",
            "Status Code": "status_code",
            "Indexability": "indexability",
            "Indexability Status": "indexability_status",
            "From": "source_page",
        }
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

        # Fill numeric columns
        if "status_code" in df.columns:
            df["status_code"] = df["status_code"].fillna(0).astype(int)

        # Analyze canonical issues
        if "url" in df.columns and "canonical_url" in df.columns:
            # Normalize for comparison
            url_lower = df["url"].str.lower().str.rstrip("/")
            canonical_lower = df["canonical_url"].fillna("").str.lower().str.rstrip("/")

            df["has_canonical"] = df["canonical_url"].notna() & (df["canonical_url"] != "")
            df["is_self_referencing"] = url_lower == canonical_lower
            df["is_canonicalized_elsewhere"] = (
                df["has_canonical"] & ~df["is_self_referencing"]
            )

        # Missing canonicals
        if "canonical_url" in df.columns:
            df["missing_canonical"] = df["canonical_url"].isna() | (
                df["canonical_url"].str.strip() == ""
            )

        return df


class CanonicalChainParser(BaseParser):
    """Parser for canonical chains (canonicals pointing to canonicals)."""

    EXPORT_NAME = "canonical_chains"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform canonical chain export."""
        mapping = {
            "Address": "url",
            "Canonical Link Element 1": "canonical_url",
            "Canonical Chain": "canonical_chain",
            "Chain Length": "chain_length",
            "Final Canonical": "final_canonical",
        }
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

        if "chain_length" in df.columns:
            df["chain_length"] = df["chain_length"].fillna(0).astype(int)
            df["has_canonical_chain"] = df["chain_length"] > 1

        return df
