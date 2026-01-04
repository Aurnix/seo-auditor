"""Redirect chain parser for Screaming Frog exports."""
import pandas as pd
from .base import BaseParser


class RedirectsParser(BaseParser):
    """Parser for redirect chain Screaming Frog exports."""

    EXPORT_NAME = "redirect_chains"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform redirect chain data to standardized format.

        Handles redirect_chains.csv export which contains:
        - Source URL
        - Redirect chain steps
        - Final destination
        - Number of redirects
        """
        mapping = {
            "Address": "url",
            "Number of Redirects": "redirect_count",
            "Redirect Chain": "redirect_chain",
            "Redirect URL 1": "redirect_url_1",
            "Redirect URL 2": "redirect_url_2",
            "Redirect URL 3": "redirect_url_3",
            "Redirect URL 4": "redirect_url_4",
            "Redirect URL 5": "redirect_url_5",
            "Final Destination": "final_destination",
            "Final Status Code": "final_status_code",
            "Status Code": "status_code",
            "From": "source_page",
        }
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

        # Fill numeric columns
        for col in ["redirect_count", "status_code", "final_status_code"]:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)

        # Identify issues
        if "redirect_count" in df.columns:
            df["has_redirect_chain"] = df["redirect_count"] > 1
            df["long_redirect_chain"] = df["redirect_count"] >= 3

        if "final_status_code" in df.columns:
            df["redirect_to_error"] = df["final_status_code"].isin([404, 410, 500, 502, 503])

        # Check for redirect loops (source == destination)
        if "url" in df.columns and "final_destination" in df.columns:
            df["is_redirect_loop"] = df["url"].str.lower() == df["final_destination"].str.lower()

        return df


class RedirectsAllParser(BaseParser):
    """Parser for all redirects export."""

    EXPORT_NAME = "redirects"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform all redirects export."""
        mapping = {
            "Address": "url",
            "Status Code": "status_code",
            "Redirect URL": "redirect_url",
            "Redirect Type": "redirect_type",
            "From": "source_page",
            "Inlinks": "inlinks",
        }
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

        if "status_code" in df.columns:
            df["status_code"] = df["status_code"].fillna(0).astype(int)

        if "inlinks" in df.columns:
            df["inlinks"] = df["inlinks"].fillna(0).astype(int)

        # Classify redirect types
        if "status_code" in df.columns:
            df["is_301"] = df["status_code"] == 301
            df["is_302"] = df["status_code"] == 302
            df["is_307"] = df["status_code"] == 307
            df["is_308"] = df["status_code"] == 308
            df["is_meta_refresh"] = df["status_code"] == 0  # Meta refresh shows as 0

        return df
