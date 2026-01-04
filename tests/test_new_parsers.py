"""Tests for new parsers (images, redirects, canonicals)."""
import pandas as pd
import pytest
from seo_auditor.ingestion.parsers.images import (
    ImagesParser,
    MissingAltTextParser,
    OversizedImagesParser,
)
from seo_auditor.ingestion.parsers.redirects import RedirectsParser, RedirectsAllParser
from seo_auditor.ingestion.parsers.canonicals import CanonicalsParser, CanonicalChainParser


class TestImagesParser:
    """Tests for ImagesParser."""

    @pytest.fixture
    def parser(self):
        return ImagesParser()

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "Address": ["https://example.com/image1.jpg", "https://example.com/image2.png"],
            "Src": ["/images/logo.jpg", "/images/banner.png"],
            "Alt Text": ["Company Logo", ""],
            "Size": [50000, 150000],
            "File Extension": ["jpg", "webp"],
        })

    def test_transform_renames_columns(self, parser, sample_df):
        """Columns are renamed correctly."""
        result = parser.transform(sample_df)

        assert "url" in result.columns
        assert "image_src" in result.columns
        assert "alt_text" in result.columns
        assert "size_bytes" in result.columns

    def test_transform_identifies_missing_alt(self, parser, sample_df):
        """Missing alt text is flagged."""
        result = parser.transform(sample_df)

        assert "missing_alt" in result.columns
        assert result["missing_alt"].iloc[0] == False  # Has alt text
        assert result["missing_alt"].iloc[1] == True  # Empty alt text

    def test_transform_identifies_oversized(self, parser, sample_df):
        """Oversized images (>100KB) are flagged."""
        result = parser.transform(sample_df)

        assert "oversized" in result.columns
        assert result["oversized"].iloc[0] == False  # 50KB
        assert result["oversized"].iloc[1] == True  # 150KB

    def test_transform_identifies_modern_formats(self, parser, sample_df):
        """Modern image formats are identified."""
        result = parser.transform(sample_df)

        assert "is_modern_format" in result.columns
        assert result["is_modern_format"].iloc[0] == False  # jpg
        assert result["is_modern_format"].iloc[1] == True  # webp


class TestMissingAltTextParser:
    """Tests for MissingAltTextParser."""

    @pytest.fixture
    def parser(self):
        return MissingAltTextParser()

    def test_transform_marks_all_as_missing(self, parser):
        """All rows are marked as missing alt."""
        df = pd.DataFrame({
            "Address": ["https://example.com/img.jpg"],
            "Src": ["/images/test.jpg"],
            "From": ["https://example.com/page"],
        })
        result = parser.transform(df)

        assert result["missing_alt"].iloc[0] == True


class TestOversizedImagesParser:
    """Tests for OversizedImagesParser."""

    @pytest.fixture
    def parser(self):
        return OversizedImagesParser()

    def test_transform_calculates_size_kb(self, parser):
        """Size in KB is calculated."""
        df = pd.DataFrame({
            "Address": ["https://example.com/big.jpg"],
            "Size": [204800],  # 200KB
        })
        result = parser.transform(df)

        assert "size_kb" in result.columns
        assert result["size_kb"].iloc[0] == 200.0
        assert result["oversized"].iloc[0] == True


class TestRedirectsParser:
    """Tests for RedirectsParser."""

    @pytest.fixture
    def parser(self):
        return RedirectsParser()

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "Address": [
                "https://example.com/old",
                "https://example.com/chain",
            ],
            "Number of Redirects": [1, 4],
            "Final Destination": [
                "https://example.com/new",
                "https://example.com/final",
            ],
            "Final Status Code": [200, 404],
        })

    def test_transform_renames_columns(self, parser, sample_df):
        """Columns are renamed correctly."""
        result = parser.transform(sample_df)

        assert "url" in result.columns
        assert "redirect_count" in result.columns
        assert "final_destination" in result.columns

    def test_transform_identifies_redirect_chains(self, parser, sample_df):
        """Redirect chains are identified."""
        result = parser.transform(sample_df)

        assert "has_redirect_chain" in result.columns
        assert result["has_redirect_chain"].iloc[0] == False  # 1 redirect
        assert result["has_redirect_chain"].iloc[1] == True  # 4 redirects

    def test_transform_identifies_long_chains(self, parser, sample_df):
        """Long redirect chains (>=3) are flagged."""
        result = parser.transform(sample_df)

        assert "long_redirect_chain" in result.columns
        assert result["long_redirect_chain"].iloc[0] == False
        assert result["long_redirect_chain"].iloc[1] == True

    def test_transform_identifies_redirect_to_error(self, parser, sample_df):
        """Redirects to error pages are flagged."""
        result = parser.transform(sample_df)

        assert "redirect_to_error" in result.columns
        assert result["redirect_to_error"].iloc[0] == False  # 200
        assert result["redirect_to_error"].iloc[1] == True  # 404


class TestRedirectsAllParser:
    """Tests for RedirectsAllParser."""

    @pytest.fixture
    def parser(self):
        return RedirectsAllParser()

    def test_transform_classifies_redirect_types(self, parser):
        """Redirect types are classified."""
        df = pd.DataFrame({
            "Address": [
                "https://example.com/a",
                "https://example.com/b",
                "https://example.com/c",
            ],
            "Status Code": [301, 302, 307],
        })
        result = parser.transform(df)

        assert result["is_301"].iloc[0] == True
        assert result["is_302"].iloc[1] == True
        assert result["is_307"].iloc[2] == True


class TestCanonicalsParser:
    """Tests for CanonicalsParser."""

    @pytest.fixture
    def parser(self):
        return CanonicalsParser()

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "Address": [
                "https://example.com/page1",
                "https://example.com/page2",
                "https://example.com/page3",
            ],
            "Canonical Link Element 1": [
                "https://example.com/page1",  # Self-referencing
                "https://example.com/main",  # Points elsewhere
                "",  # Missing
            ],
        })

    def test_transform_renames_columns(self, parser, sample_df):
        """Columns are renamed correctly."""
        result = parser.transform(sample_df)

        assert "url" in result.columns
        assert "canonical_url" in result.columns

    def test_transform_identifies_self_referencing(self, parser, sample_df):
        """Self-referencing canonicals are identified."""
        result = parser.transform(sample_df)

        assert "is_self_referencing" in result.columns
        assert result["is_self_referencing"].iloc[0] == True
        assert result["is_self_referencing"].iloc[1] == False

    def test_transform_identifies_canonicalized_elsewhere(self, parser, sample_df):
        """Pages canonicalized to other URLs are identified."""
        result = parser.transform(sample_df)

        assert "is_canonicalized_elsewhere" in result.columns
        assert result["is_canonicalized_elsewhere"].iloc[0] == False
        assert result["is_canonicalized_elsewhere"].iloc[1] == True

    def test_transform_identifies_missing_canonical(self, parser, sample_df):
        """Missing canonicals are identified."""
        result = parser.transform(sample_df)

        assert "missing_canonical" in result.columns
        assert result["missing_canonical"].iloc[0] == False
        assert result["missing_canonical"].iloc[2] == True


class TestCanonicalChainParser:
    """Tests for CanonicalChainParser."""

    @pytest.fixture
    def parser(self):
        return CanonicalChainParser()

    def test_transform_identifies_chains(self, parser):
        """Canonical chains are identified."""
        df = pd.DataFrame({
            "Address": ["https://example.com/page"],
            "Chain Length": [3],
        })
        result = parser.transform(df)

        assert "has_canonical_chain" in result.columns
        assert result["has_canonical_chain"].iloc[0] == True
