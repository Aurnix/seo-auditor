"""Main SF parser orchestrator."""
from pathlib import Path
from typing import Optional
import pandas as pd
from ..utils.url import normalize_url
from .parsers.internal_html import InternalHTMLParser
from .parsers.images import ImagesParser, MissingAltTextParser, OversizedImagesParser
from .parsers.redirects import RedirectsParser, RedirectsAllParser
from .parsers.canonicals import CanonicalsParser


class SFParser:
    """Orchestrates parsing of all Screaming Frog export files."""

    def __init__(self):
        self.internal_html = InternalHTMLParser()
        self.images = ImagesParser()
        self.missing_alt = MissingAltTextParser()
        self.oversized_images = OversizedImagesParser()
        self.redirects = RedirectsParser()
        self.redirects_all = RedirectsAllParser()
        self.canonicals = CanonicalsParser()

    def parse_export(self, export_dir: Path) -> pd.DataFrame:
        """Parse all available export files and return merged DataFrame.

        Args:
            export_dir: Path to Screaming Frog export directory

        Returns:
            DataFrame with all parsed data, normalized URLs
        """
        # Primary HTML data (required)
        html_files = ["internal_html.csv", "internal_all.csv"]
        for filename in html_files:
            path = export_dir / filename
            if path.exists():
                self.internal_html.parse(path)
                break

        if self.internal_html.data is None:
            return pd.DataFrame()

        df = self.internal_html.data.copy()
        df["url_normalized"] = df["url"].apply(normalize_url)

        # Parse supplementary data
        self._parse_images(export_dir)
        self._parse_redirects(export_dir)
        self._parse_canonicals(export_dir)

        # Merge image issues into main dataframe
        df = self._merge_image_issues(df)

        # Merge redirect data
        df = self._merge_redirect_data(df)

        # Merge canonical data
        df = self._merge_canonical_data(df)

        return df

    def _parse_images(self, export_dir: Path) -> None:
        """Parse all image-related exports."""
        image_files = [
            ("all_images.csv", self.images),
            ("images_missing_alt_text.csv", self.missing_alt),
            ("images_over_100kb.csv", self.oversized_images),
        ]
        for filename, parser in image_files:
            path = export_dir / filename
            if path.exists():
                parser.parse(path)

    def _parse_redirects(self, export_dir: Path) -> None:
        """Parse redirect-related exports."""
        redirect_files = [
            ("redirect_chains.csv", self.redirects),
            ("redirects.csv", self.redirects_all),
        ]
        for filename, parser in redirect_files:
            path = export_dir / filename
            if path.exists():
                parser.parse(path)

    def _parse_canonicals(self, export_dir: Path) -> None:
        """Parse canonical-related exports."""
        path = export_dir / "canonicals.csv"
        if path.exists():
            self.canonicals.parse(path)

    def _merge_image_issues(self, df: pd.DataFrame) -> pd.DataFrame:
        """Merge image issue counts into main dataframe."""
        # Count missing alt text per page
        if self.missing_alt.data is not None and not self.missing_alt.data.empty:
            if "source_page" in self.missing_alt.data.columns:
                alt_counts = (
                    self.missing_alt.data.groupby("source_page")
                    .size()
                    .reset_index(name="images_missing_alt")
                )
                alt_counts["source_page_normalized"] = alt_counts["source_page"].apply(
                    normalize_url
                )
                df = df.merge(
                    alt_counts[["source_page_normalized", "images_missing_alt"]],
                    left_on="url_normalized",
                    right_on="source_page_normalized",
                    how="left",
                )
                df["images_missing_alt"] = df["images_missing_alt"].fillna(0).astype(int)
                df = df.drop(columns=["source_page_normalized"], errors="ignore")

        # Count oversized images per page
        if self.oversized_images.data is not None and not self.oversized_images.data.empty:
            if "source_page" in self.oversized_images.data.columns:
                size_counts = (
                    self.oversized_images.data.groupby("source_page")
                    .size()
                    .reset_index(name="images_oversized")
                )
                size_counts["source_page_normalized"] = size_counts["source_page"].apply(
                    normalize_url
                )
                df = df.merge(
                    size_counts[["source_page_normalized", "images_oversized"]],
                    left_on="url_normalized",
                    right_on="source_page_normalized",
                    how="left",
                )
                df["images_oversized"] = df["images_oversized"].fillna(0).astype(int)
                df = df.drop(columns=["source_page_normalized"], errors="ignore")

        return df

    def _merge_redirect_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Merge redirect chain data into main dataframe."""
        if self.redirects.data is not None and not self.redirects.data.empty:
            redirect_df = self.redirects.data
            if "url" in redirect_df.columns:
                redirect_df["url_normalized"] = redirect_df["url"].apply(normalize_url)

                # Select relevant columns
                cols = ["url_normalized"]
                for col in ["redirect_count", "has_redirect_chain", "long_redirect_chain"]:
                    if col in redirect_df.columns:
                        cols.append(col)

                if len(cols) > 1:
                    redirect_subset = redirect_df[cols].drop_duplicates(
                        subset=["url_normalized"]
                    )
                    df = df.merge(redirect_subset, on="url_normalized", how="left")

                    if "redirect_count" in df.columns:
                        df["redirect_count"] = df["redirect_count"].fillna(0).astype(int)
                    for col in ["has_redirect_chain", "long_redirect_chain"]:
                        if col in df.columns:
                            df[col] = df[col].fillna(False)

        return df

    def _merge_canonical_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Merge canonical data into main dataframe."""
        if self.canonicals.data is not None and not self.canonicals.data.empty:
            canon_df = self.canonicals.data
            if "url" in canon_df.columns:
                canon_df["url_normalized"] = canon_df["url"].apply(normalize_url)

                # Select relevant columns
                cols = ["url_normalized"]
                for col in [
                    "canonical_url",
                    "has_canonical",
                    "is_self_referencing",
                    "missing_canonical",
                ]:
                    if col in canon_df.columns:
                        cols.append(col)

                if len(cols) > 1:
                    canon_subset = canon_df[cols].drop_duplicates(subset=["url_normalized"])
                    df = df.merge(canon_subset, on="url_normalized", how="left")

                    for col in ["has_canonical", "is_self_referencing", "missing_canonical"]:
                        if col in df.columns:
                            df[col] = df[col].fillna(False)

        return df

    def get_image_data(self) -> Optional[pd.DataFrame]:
        """Get raw image data if available."""
        return self.images.data

    def get_redirect_data(self) -> Optional[pd.DataFrame]:
        """Get raw redirect data if available."""
        return self.redirects.data

    def get_canonical_data(self) -> Optional[pd.DataFrame]:
        """Get raw canonical data if available."""
        return self.canonicals.data
