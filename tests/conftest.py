"""Shared pytest fixtures."""
import os
import pytest
import pandas as pd

# Set test environment variables before importing modules
os.environ.setdefault("SEO_AUDITOR_ANTHROPIC_API_KEY", "test-key-for-testing")


@pytest.fixture
def sample_crawl_df():
    """Create a sample crawl DataFrame for testing."""
    return pd.DataFrame({
        "url": [
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/products",
            "https://example.com/contact",
            "https://example.com/blog/post-1",
        ],
        "url_normalized": [
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/products",
            "https://example.com/contact",
            "https://example.com/blog/post-1",
        ],
        "status_code": [200, 200, 200, 404, 200],
        "content_type": ["text/html"] * 5,
        "indexability": ["indexable", "indexable", "indexable", "non_indexable", "indexable"],
        "title": ["Home", "About Us", None, "Contact", "Blog Post 1"],
        "title_length": [4, 8, 0, 7, 11],
        "meta_description": ["Welcome", "About", "Products", None, "Blog"],
        "meta_description_length": [7, 5, 8, 0, 4],
        "h1": ["Welcome", "About", "Products", "Contact", None],
        "h1_count": [1, 1, 1, 1, 0],
        "word_count": [500, 300, 100, 200, 1000],
        "crawl_depth": [0, 1, 1, 2, 2],
        "internal_links_in": [10, 5, 8, 2, 3],
        "internal_links_out": [5, 3, 4, 1, 2],
        "clicks": [1000, 500, 200, 0, 50],
        "impressions": [10000, 5000, 2000, 100, 500],
        "ctr": [0.1, 0.1, 0.1, 0.0, 0.1],
        "avg_position": [5.0, 10.0, 15.0, 50.0, 20.0],
    })


@pytest.fixture
def sample_gsc_df():
    """Create a sample GSC DataFrame for testing."""
    return pd.DataFrame({
        "page": [
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/products",
        ],
        "clicks": [1000, 500, 200],
        "impressions": [10000, 5000, 2000],
        "ctr": [0.1, 0.1, 0.1],
        "position": [5.0, 10.0, 15.0],
    })


@pytest.fixture
def empty_df():
    """Create an empty DataFrame with expected columns."""
    return pd.DataFrame(columns=[
        "url", "status_code", "title", "meta_description",
        "h1", "word_count", "crawl_depth", "clicks", "impressions"
    ])


@pytest.fixture
def large_crawl_df():
    """Create a larger crawl DataFrame for chunking tests."""
    n = 1000
    return pd.DataFrame({
        "url": [f"https://example.com/page{i}" for i in range(n)],
        "status_code": [200] * int(n * 0.9) + [404] * int(n * 0.05) + [500] * int(n * 0.05),
        "title": ["Title"] * int(n * 0.8) + [None] * int(n * 0.2),
        "word_count": [500] * int(n * 0.5) + [100] * int(n * 0.5),
        "clicks": list(range(n)),
        "impressions": [i * 10 for i in range(n)],
    })
