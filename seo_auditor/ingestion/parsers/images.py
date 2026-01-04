"""Image data parser for Screaming Frog exports."""
import pandas as pd
from .base import BaseParser


class ImagesParser(BaseParser):
    """Parser for image-related Screaming Frog exports."""

    EXPORT_NAME = "images"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform image data to standardized format.

        Handles multiple SF export files:
        - images_missing_alt_text.csv
        - images_over_100kb.csv
        - all_images.csv (internal images)
        """
        mapping = {
            "Address": "url",
            "Src": "image_src",
            "Alt Text": "alt_text",
            "Alt Text Length": "alt_text_length",
            "Size": "size_bytes",
            "Status Code": "status_code",
            "Content": "content_type",
            "File Extension": "file_extension",
            "Width": "width",
            "Height": "height",
            "From": "source_page",
            "Type": "image_type",
        }
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

        # Fill numeric columns
        for col in ["size_bytes", "status_code", "width", "height", "alt_text_length"]:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(int)

        # Identify issues
        if "alt_text" in df.columns:
            df["missing_alt"] = df["alt_text"].isna() | (df["alt_text"].str.strip() == "")

        if "size_bytes" in df.columns:
            df["oversized"] = df["size_bytes"] > 100 * 1024  # > 100KB

        if "file_extension" in df.columns:
            df["is_modern_format"] = df["file_extension"].str.lower().isin(
                ["webp", "avif", "svg"]
            )

        return df


class MissingAltTextParser(BaseParser):
    """Parser specifically for images missing alt text."""

    EXPORT_NAME = "images_missing_alt_text"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform missing alt text export."""
        mapping = {
            "Address": "url",
            "Src": "image_src",
            "Alt Text": "alt_text",
            "From": "source_page",
            "Size": "size_bytes",
        }
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

        if "size_bytes" in df.columns:
            df["size_bytes"] = df["size_bytes"].fillna(0).astype(int)

        df["missing_alt"] = True
        return df


class OversizedImagesParser(BaseParser):
    """Parser for images over 100KB."""

    EXPORT_NAME = "images_over_100kb"

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform oversized images export."""
        mapping = {
            "Address": "url",
            "Src": "image_src",
            "Size": "size_bytes",
            "Content": "content_type",
            "Status Code": "status_code",
            "From": "source_page",
        }
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

        if "size_bytes" in df.columns:
            df["size_bytes"] = df["size_bytes"].fillna(0).astype(int)
            df["size_kb"] = df["size_bytes"] / 1024

        df["oversized"] = True
        return df
