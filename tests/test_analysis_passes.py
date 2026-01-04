"""Tests for analysis passes."""
from unittest.mock import AsyncMock, MagicMock, patch
import json
import pandas as pd
import pytest
from seo_auditor.analysis.passes.technical import TechnicalAnalyzer
from seo_auditor.analysis.passes.content import ContentAnalyzer
from seo_auditor.analysis.passes.links import LinksAnalyzer
from seo_auditor.analysis.passes.performance import PerformanceAnalyzer
from seo_auditor.clients.claude_client import AnalysisResult
from seo_auditor.models.enums import AnalysisPassType


class TestTechnicalAnalyzer:
    """Tests for TechnicalAnalyzer."""

    @pytest.fixture
    def mock_claude_client(self):
        """Create a mock Claude client."""
        client = MagicMock()
        client.analyze = AsyncMock()
        return client

    @pytest.fixture
    def analyzer(self, mock_claude_client):
        """Create a TechnicalAnalyzer with mocked client."""
        return TechnicalAnalyzer(mock_claude_client)

    def test_pass_type(self, analyzer):
        """Analyzer has correct pass type."""
        assert analyzer.PASS_TYPE == AnalysisPassType.TECHNICAL

    def test_prompt_file(self, analyzer):
        """Analyzer uses correct prompt file."""
        assert analyzer.PROMPT_FILE == "technical.md"

    def test_prepare_data_selects_columns(self, analyzer, sample_crawl_df):
        """_prepare_data selects relevant columns."""
        result = analyzer._prepare_data(sample_crawl_df)

        assert "url" in result.columns
        assert "status_code" in result.columns
        assert "indexability" in result.columns
        assert "crawl_depth" in result.columns
        # Should not include content columns
        assert "word_count" not in result.columns

    async def test_analyze_returns_result(self, analyzer, mock_claude_client, sample_crawl_df):
        """analyze() returns AnalysisPassResult."""
        mock_claude_client.analyze.return_value = AnalysisResult(
            content=json.dumps({
                "issues": [
                    {
                        "id": "tech_001",
                        "category": "technical",
                        "title": "404 Errors",
                        "description": "Found pages returning 404",
                        "impact": "Users cannot access content",
                        "priority": "high",
                        "effort": "moderate",
                        "affected_urls": ["https://example.com/contact"],
                        "affected_count": 1,
                        "recommendation": "Fix or redirect broken URLs",
                        "implementation_steps": ["Identify broken URLs", "Create redirects"],
                    }
                ],
                "summary": "Found 1 technical issue",
                "health_score": 85,
            }),
            input_tokens=500,
            output_tokens=200,
            model="claude-sonnet-4-20250514",
        )

        result = await analyzer.analyze(sample_crawl_df)

        assert result.pass_type == AnalysisPassType.TECHNICAL
        assert len(result.issues) == 1
        assert result.issues[0].title == "404 Errors"
        assert result.input_tokens == 500
        assert result.output_tokens == 200


class TestContentAnalyzer:
    """Tests for ContentAnalyzer."""

    @pytest.fixture
    def mock_claude_client(self):
        client = MagicMock()
        client.analyze = AsyncMock()
        return client

    @pytest.fixture
    def analyzer(self, mock_claude_client):
        return ContentAnalyzer(mock_claude_client)

    def test_pass_type(self, analyzer):
        assert analyzer.PASS_TYPE == AnalysisPassType.CONTENT

    def test_prompt_file(self, analyzer):
        assert analyzer.PROMPT_FILE == "content.md"


class TestLinksAnalyzer:
    """Tests for LinksAnalyzer."""

    @pytest.fixture
    def mock_claude_client(self):
        client = MagicMock()
        client.analyze = AsyncMock()
        return client

    @pytest.fixture
    def analyzer(self, mock_claude_client):
        return LinksAnalyzer(mock_claude_client)

    def test_pass_type(self, analyzer):
        assert analyzer.PASS_TYPE == AnalysisPassType.LINKS

    def test_prompt_file(self, analyzer):
        assert analyzer.PROMPT_FILE == "links.md"


class TestPerformanceAnalyzer:
    """Tests for PerformanceAnalyzer."""

    @pytest.fixture
    def mock_claude_client(self):
        client = MagicMock()
        client.analyze = AsyncMock()
        return client

    @pytest.fixture
    def analyzer(self, mock_claude_client):
        return PerformanceAnalyzer(mock_claude_client)

    def test_pass_type(self, analyzer):
        assert analyzer.PASS_TYPE == AnalysisPassType.PERFORMANCE

    def test_prompt_file(self, analyzer):
        assert analyzer.PROMPT_FILE == "performance.md"


class TestBaseAnalysisPassParsing:
    """Tests for response parsing in BaseAnalysisPass."""

    @pytest.fixture
    def mock_claude_client(self):
        client = MagicMock()
        client.analyze = AsyncMock()
        return client

    @pytest.fixture
    def analyzer(self, mock_claude_client):
        return TechnicalAnalyzer(mock_claude_client)

    def test_parse_json_response(self, analyzer):
        """Parses valid JSON response."""
        content = '{"issues": [{"id": "test"}], "summary": "Test"}'
        result = analyzer._parse_response(content)

        assert "issues" in result
        assert len(result["issues"]) == 1

    def test_parse_json_in_code_block(self, analyzer):
        """Parses JSON from markdown code block."""
        content = '''Here's the analysis:

```json
{"issues": [{"id": "test"}], "summary": "Test"}
```

That's all.'''
        result = analyzer._parse_response(content)

        assert "issues" in result
        assert len(result["issues"]) == 1

    def test_parse_invalid_json(self, analyzer):
        """Returns empty issues for invalid JSON."""
        content = "This is not valid JSON at all"
        result = analyzer._parse_response(content)

        assert result == {"issues": []}

    def test_convert_issues_basic(self, analyzer):
        """Converts raw issue dicts to SEOIssue objects."""
        raw = [
            {
                "id": "tech_001",
                "category": "technical",
                "title": "Test Issue",
                "description": "Description",
                "impact": "Impact",
                "priority": "high",
                "effort": "quick_win",
                "affected_urls": ["https://example.com/1"],
                "affected_count": 1,
                "recommendation": "Fix it",
                "implementation_steps": ["Step 1"],
            }
        ]
        result = analyzer._convert_issues(raw)

        assert len(result) == 1
        assert result[0].id == "tech_001"
        assert result[0].title == "Test Issue"

    def test_convert_issues_handles_url_objects(self, analyzer):
        """Converts affected URLs that are objects."""
        raw = [
            {
                "id": "test",
                "category": "technical",
                "title": "Test",
                "description": "Test",
                "impact": "Test",
                "priority": "medium",
                "effort": "moderate",
                "affected_urls": [
                    {"url": "https://example.com/1", "details": {"error": "404"}},
                ],
                "recommendation": "Fix",
            }
        ]
        result = analyzer._convert_issues(raw)

        assert len(result) == 1
        assert result[0].affected_urls[0].url == "https://example.com/1"

    def test_convert_issues_limits_urls(self, analyzer):
        """Limits affected URLs to 50."""
        raw = [
            {
                "id": "test",
                "category": "technical",
                "title": "Test",
                "description": "Test",
                "impact": "Test",
                "priority": "medium",
                "effort": "moderate",
                "affected_urls": [f"https://example.com/{i}" for i in range(100)],
                "recommendation": "Fix",
            }
        ]
        result = analyzer._convert_issues(raw)

        assert len(result[0].affected_urls) == 50

    def test_convert_issues_handles_missing_fields(self, analyzer):
        """Handles issues with missing optional fields."""
        raw = [
            {
                "title": "Minimal Issue",
            }
        ]
        result = analyzer._convert_issues(raw)

        assert len(result) == 1
        assert result[0].title == "Minimal Issue"
        assert result[0].description == ""
        assert result[0].affected_urls == []
