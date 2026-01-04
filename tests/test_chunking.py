"""Tests for data chunking."""
import pandas as pd
import pytest
from seo_auditor.analysis.chunking import DataChunk, DataChunker


class TestDataChunk:
    """Tests for DataChunk."""

    @pytest.fixture
    def chunk(self):
        return DataChunk(
            chunk_id=1,
            total_chunks=3,
            total_urls=100,
            stats={"total_urls": 100, "status_codes": {200: 90, 404: 10}},
            urls=[],
            issue_samples={
                "missing_title": [{"url": "https://example.com/page1", "title": None}],
                "thin_content": [],
            },
        )

    def test_to_prompt_context_includes_header(self, chunk):
        """Prompt context includes chunk header."""
        result = chunk.to_prompt_context()
        assert "## Data Chunk 1/3" in result

    def test_to_prompt_context_includes_stats(self, chunk):
        """Prompt context includes statistics."""
        result = chunk.to_prompt_context()
        assert "### Statistics" in result
        assert "total_urls" in result

    def test_to_prompt_context_includes_samples(self, chunk):
        """Prompt context includes issue samples."""
        result = chunk.to_prompt_context()
        assert "### Issue Samples" in result
        assert "missing_title" in result

    def test_to_prompt_context_skips_empty_samples(self, chunk):
        """Empty sample categories are skipped."""
        result = chunk.to_prompt_context()
        # thin_content is empty, should not appear as section
        assert "thin_content" not in result or "[]" not in result.split("thin_content")[1][:50]


class TestDataChunker:
    """Tests for DataChunker."""

    @pytest.fixture
    def chunker(self):
        return DataChunker(max_urls=500)

    @pytest.fixture
    def sample_df(self):
        """Create sample crawl data."""
        return pd.DataFrame({
            "url": [f"https://example.com/page{i}" for i in range(100)],
            "status_code": [200] * 90 + [404] * 10,
            "title": ["Page Title"] * 50 + [None] * 50,
            "word_count": [500] * 30 + [100] * 70,
            "clicks": [10] * 20 + [0] * 80,
        })

    def test_chunk_for_analysis_returns_iterator(self, chunker, sample_df):
        """chunk_for_analysis returns an iterator."""
        result = chunker.chunk_for_analysis(sample_df)
        assert hasattr(result, "__iter__")

    def test_chunk_for_analysis_produces_chunks(self, chunker, sample_df):
        """chunk_for_analysis produces DataChunk objects."""
        chunks = list(chunker.chunk_for_analysis(sample_df))
        assert len(chunks) >= 1
        assert isinstance(chunks[0], DataChunk)

    def test_chunk_includes_statistics(self, chunker, sample_df):
        """Chunks include calculated statistics."""
        chunks = list(chunker.chunk_for_analysis(sample_df))
        chunk = chunks[0]

        assert "total_urls" in chunk.stats
        assert chunk.stats["total_urls"] == 100

    def test_chunk_includes_status_code_counts(self, chunker, sample_df):
        """Chunks include status code distribution."""
        chunks = list(chunker.chunk_for_analysis(sample_df))
        chunk = chunks[0]

        assert "status_codes" in chunk.stats
        assert 200 in chunk.stats["status_codes"]
        assert chunk.stats["status_codes"][200] == 90

    def test_chunk_includes_click_totals(self, chunker, sample_df):
        """Chunks include total clicks."""
        chunks = list(chunker.chunk_for_analysis(sample_df))
        chunk = chunks[0]

        assert "total_clicks" in chunk.stats
        assert chunk.stats["total_clicks"] == 200  # 20 pages * 10 clicks

    def test_chunk_samples_missing_titles(self, chunker, sample_df):
        """Chunks sample pages with missing titles."""
        chunks = list(chunker.chunk_for_analysis(sample_df))
        chunk = chunks[0]

        assert "missing_title" in chunk.issue_samples
        assert len(chunk.issue_samples["missing_title"]) > 0

    def test_chunk_samples_thin_content(self, chunker, sample_df):
        """Chunks sample pages with thin content."""
        chunks = list(chunker.chunk_for_analysis(sample_df))
        chunk = chunks[0]

        assert "thin_content" in chunk.issue_samples
        # 70 pages have word_count < 300
        assert len(chunk.issue_samples["thin_content"]) > 0

    def test_chunk_limits_samples_to_ten(self, chunker, sample_df):
        """Issue samples are limited to 10."""
        chunks = list(chunker.chunk_for_analysis(sample_df))
        chunk = chunks[0]

        for samples in chunk.issue_samples.values():
            assert len(samples) <= 10

    def test_chunker_handles_empty_df(self, chunker):
        """Chunker handles empty DataFrame."""
        empty_df = pd.DataFrame(columns=["url", "status_code"])
        chunks = list(chunker.chunk_for_analysis(empty_df))

        assert len(chunks) == 1
        assert chunks[0].total_urls == 0

    def test_chunker_handles_missing_columns(self, chunker):
        """Chunker handles missing optional columns."""
        minimal_df = pd.DataFrame({
            "url": ["https://example.com"],
            "status_code": [200],
        })
        chunks = list(chunker.chunk_for_analysis(minimal_df))

        assert len(chunks) == 1
        # Should not error on missing columns
        assert chunks[0].stats["total_urls"] == 1
