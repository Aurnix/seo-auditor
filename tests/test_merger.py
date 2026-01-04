"""Tests for data merger."""
import pandas as pd
import pytest
from seo_auditor.ingestion.merger import DataMerger


class TestDataMerger:
    """Tests for DataMerger."""

    @pytest.fixture
    def merger(self):
        return DataMerger()

    @pytest.fixture
    def sf_data(self):
        """Sample Screaming Frog data."""
        return pd.DataFrame({
            "url": [
                "https://example.com/page1",
                "https://example.com/page2",
                "https://example.com/page3",
            ],
            "status_code": [200, 200, 404],
            "title": ["Page 1", "Page 2", "Page 3"],
        })

    @pytest.fixture
    def gsc_data(self):
        """Sample GSC data."""
        return pd.DataFrame({
            "page": [
                "https://example.com/page1",
                "https://example.com/page1",  # Duplicate for aggregation
                "https://example.com/page2",
            ],
            "clicks": [100, 50, 25],
            "impressions": [1000, 500, 250],
            "ctr": [0.1, 0.1, 0.1],
            "position": [5.0, 4.0, 10.0],
        })

    def test_merge_combines_data(self, merger, sf_data, gsc_data):
        """Merge combines SF and GSC data."""
        result = merger.merge(sf_data, gsc_data)

        assert len(result) == 3
        assert "clicks" in result.columns
        assert "impressions" in result.columns
        assert "url" in result.columns

    def test_merge_aggregates_gsc_data(self, merger, sf_data, gsc_data):
        """GSC data is aggregated by URL."""
        result = merger.merge(sf_data, gsc_data)

        # Page 1 should have aggregated clicks (100 + 50)
        page1 = result[result["url"] == "https://example.com/page1"]
        assert page1["clicks"].iloc[0] == 150
        assert page1["impressions"].iloc[0] == 1500

    def test_merge_fills_missing_with_zero(self, merger, sf_data, gsc_data):
        """Missing GSC data is filled with zeros."""
        result = merger.merge(sf_data, gsc_data)

        # Page 3 has no GSC data
        page3 = result[result["url"] == "https://example.com/page3"]
        assert page3["clicks"].iloc[0] == 0
        assert page3["impressions"].iloc[0] == 0

    def test_merge_calculates_has_traffic(self, merger, sf_data, gsc_data):
        """has_traffic flag is calculated correctly."""
        result = merger.merge(sf_data, gsc_data)

        page1 = result[result["url"] == "https://example.com/page1"]
        page3 = result[result["url"] == "https://example.com/page3"]

        assert page1["has_traffic"].iloc[0] == True
        assert page3["has_traffic"].iloc[0] == False

    def test_merge_calculates_priority_score(self, merger, sf_data, gsc_data):
        """Priority score is calculated."""
        result = merger.merge(sf_data, gsc_data)

        assert "priority_score" in result.columns
        # Higher traffic = higher priority
        page1 = result[result["url"] == "https://example.com/page1"]
        page3 = result[result["url"] == "https://example.com/page3"]

        assert page1["priority_score"].iloc[0] > page3["priority_score"].iloc[0]

    def test_merge_normalizes_urls(self, merger):
        """URLs are normalized before merging."""
        sf_data = pd.DataFrame({
            "url": ["https://example.com/Page/"],  # Trailing slash, mixed case
            "status_code": [200],
        })
        gsc_data = pd.DataFrame({
            "page": ["https://example.com/page"],  # No trailing slash, lowercase
            "clicks": [100],
            "impressions": [1000],
            "ctr": [0.1],
            "position": [5.0],
        })

        result = merger.merge(sf_data, gsc_data)

        # Should match despite URL differences
        assert result["clicks"].iloc[0] == 100

    def test_merge_handles_empty_gsc(self, merger, sf_data):
        """Merge handles empty GSC data."""
        gsc_data = pd.DataFrame({
            "page": [],
            "clicks": [],
            "impressions": [],
            "ctr": [],
            "position": [],
        })

        result = merger.merge(sf_data, gsc_data)

        assert len(result) == 3
        assert result["clicks"].sum() == 0

    def test_merge_preserves_sf_columns(self, merger, sf_data, gsc_data):
        """Original SF columns are preserved."""
        result = merger.merge(sf_data, gsc_data)

        assert "status_code" in result.columns
        assert "title" in result.columns
        assert result["status_code"].iloc[0] == 200
