"""Tests for data parsers."""
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from seo_auditor.ingestion.parsers.base import BaseParser
from seo_auditor.ingestion.parsers.internal_html import InternalHTMLParser
from seo_auditor.ingestion.sf_parser import SFParser


class TestBaseParser:
    """Tests for BaseParser."""

    def test_parse_nonexistent_file(self):
        """Parsing nonexistent file returns empty DataFrame."""

        class ConcreteParser(BaseParser):
            def transform(self, df):
                return df

        parser = ConcreteParser()
        result = parser.parse(Path("/nonexistent/file.csv"))
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_parse_strips_column_whitespace(self):
        """Column names are stripped of whitespace."""

        class ConcreteParser(BaseParser):
            def transform(self, df):
                return df

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("  Column1  , Column2 \n")
            f.write("value1,value2\n")
            f.flush()

            parser = ConcreteParser()
            result = parser.parse(Path(f.name))

            assert "Column1" in result.columns
            assert "Column2" in result.columns

    def test_parse_handles_malformed_csv(self):
        """Malformed CSV rows are skipped."""

        class ConcreteParser(BaseParser):
            def transform(self, df):
                return df

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\n")
            f.write("valid1,valid2\n")
            f.write("bad,row,with,extra,columns\n")
            f.write("valid3,valid4\n")
            f.flush()

            parser = ConcreteParser()
            result = parser.parse(Path(f.name))

            # Should have parsed at least the valid rows
            assert len(result) >= 2


class TestInternalHTMLParser:
    """Tests for InternalHTMLParser."""

    @pytest.fixture
    def parser(self):
        return InternalHTMLParser()

    @pytest.fixture
    def sample_df(self):
        """Create sample Screaming Frog-like data."""
        return pd.DataFrame({
            "Address": ["https://example.com/page1", "https://example.com/page2"],
            "Status Code": [200, 404],
            "Content Type": ["text/html", "text/html"],
            "Indexability": ["Indexable", "Non-Indexable"],
            "Title 1": ["Page Title 1", None],
            "Title 1 Length": [13, 0],
            "Meta Description 1": ["Description 1", "Description 2"],
            "Meta Description 1 Length": [13, 13],
            "H1-1": ["Heading 1", "Heading 2"],
            "H1-1 Length": [9, 9],
            "Word Count": [500, 100],
            "Crawl Depth": [1, 2],
            "Inlinks": [10, 5],
            "Outlinks": [3, 2],
        })

    def test_transform_renames_columns(self, parser, sample_df):
        """Columns are renamed to standardized names."""
        result = parser.transform(sample_df)

        assert "url" in result.columns
        assert "status_code" in result.columns
        assert "title" in result.columns
        assert "meta_description" in result.columns
        assert "h1" in result.columns
        assert "word_count" in result.columns
        assert "crawl_depth" in result.columns

    def test_transform_preserves_values(self, parser, sample_df):
        """Values are preserved after transformation."""
        result = parser.transform(sample_df)

        assert result["url"].iloc[0] == "https://example.com/page1"
        assert result["status_code"].iloc[0] == 200
        assert result["title"].iloc[0] == "Page Title 1"

    def test_transform_counts_h1_tags(self, parser):
        """H1 count is calculated correctly.

        Note: H1-1 gets renamed to 'h1', so only H1-2, H1-3, etc. remain
        as 'H1-' prefixed columns for counting. The count represents
        additional H1 tags beyond the first one.
        """
        df = pd.DataFrame({
            "Address": ["https://example.com/page"],
            "H1-1": ["First H1"],
            "H1-2": ["Second H1"],
            "H1-3": ["Third H1"],
            "H1-4": [None],
        })
        result = parser.transform(df)

        # H1-1 is renamed to 'h1', so h1_count includes H1-2 and H1-3 (not H1-4 which is None)
        assert result["h1_count"].iloc[0] == 2

    def test_transform_fills_na_with_zero(self, parser):
        """NaN values in numeric columns are filled with 0."""
        df = pd.DataFrame({
            "Address": ["https://example.com/page"],
            "Status Code": [None],
            "Word Count": [None],
            "Crawl Depth": [None],
        })
        result = parser.transform(df)

        assert result["status_code"].iloc[0] == 0
        assert result["word_count"].iloc[0] == 0
        assert result["crawl_depth"].iloc[0] == 0


class TestSFParser:
    """Tests for SFParser orchestrator."""

    @pytest.fixture
    def parser(self):
        return SFParser()

    def test_parse_export_with_no_files(self, parser):
        """Parsing empty directory returns empty DataFrame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = parser.parse_export(Path(tmpdir))
            assert isinstance(result, pd.DataFrame)
            assert result.empty

    def test_parse_export_with_internal_html(self, parser):
        """Parses internal_html.csv correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "internal_html.csv"
            csv_path.write_text(
                "Address,Status Code,Title 1\n"
                "https://example.com,200,Home Page\n"
            )

            result = parser.parse_export(Path(tmpdir))

            assert len(result) == 1
            assert result["url"].iloc[0] == "https://example.com"
            assert "url_normalized" in result.columns

    def test_parse_export_prefers_internal_html(self, parser):
        """Prefers internal_html.csv over internal_all.csv."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create both files
            html_path = Path(tmpdir) / "internal_html.csv"
            html_path.write_text(
                "Address,Status Code,Title 1\n"
                "https://example.com/html,200,HTML Page\n"
            )

            all_path = Path(tmpdir) / "internal_all.csv"
            all_path.write_text(
                "Address,Status Code,Title 1\n"
                "https://example.com/all,200,All Page\n"
            )

            result = parser.parse_export(Path(tmpdir))

            # Should use internal_html.csv
            assert "html" in result["url"].iloc[0]
