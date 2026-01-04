"""Tests for URL utilities."""
import pytest
from seo_auditor.utils.url import normalize_url


class TestNormalizeUrl:
    """Tests for URL normalization."""

    def test_normalize_basic_url(self):
        """Basic URL normalization."""
        assert normalize_url("https://example.com") == "https://example.com/"

    def test_normalize_removes_trailing_slash(self):
        """Trailing slashes are normalized."""
        assert normalize_url("https://example.com/page/") == "https://example.com/page"

    def test_normalize_preserves_path(self):
        """Paths are preserved."""
        assert normalize_url("https://example.com/path/to/page") == "https://example.com/path/to/page"

    def test_normalize_lowercases_url(self):
        """URLs are lowercased."""
        assert normalize_url("HTTPS://EXAMPLE.COM/Page") == "https://example.com/page"

    def test_normalize_strips_whitespace(self):
        """Whitespace is stripped."""
        assert normalize_url("  https://example.com/page  ") == "https://example.com/page"

    def test_normalize_empty_string(self):
        """Empty strings return empty."""
        assert normalize_url("") == ""

    def test_normalize_none_handling(self):
        """None-like values return empty."""
        assert normalize_url(None) == ""

    def test_normalize_http_url(self):
        """HTTP URLs are handled."""
        assert normalize_url("http://example.com/page") == "http://example.com/page"

    def test_normalize_root_path(self):
        """Root paths get trailing slash."""
        assert normalize_url("https://example.com") == "https://example.com/"
        assert normalize_url("https://example.com/") == "https://example.com/"

    def test_normalize_with_query_params(self):
        """Query params are stripped (path only)."""
        result = normalize_url("https://example.com/page?foo=bar")
        # The current implementation strips query params
        assert result == "https://example.com/page"

    def test_normalize_with_port(self):
        """URLs with ports are handled."""
        assert normalize_url("https://example.com:8080/page") == "https://example.com:8080/page"
