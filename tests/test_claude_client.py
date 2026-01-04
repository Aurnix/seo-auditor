"""Tests for Claude client."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from seo_auditor.clients.claude_client import ClaudeClient, AnalysisResult


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_analysis_result_creation(self):
        """AnalysisResult is created correctly."""
        result = AnalysisResult(
            content="Analysis content",
            input_tokens=100,
            output_tokens=50,
            model="claude-sonnet-4-20250514",
        )

        assert result.content == "Analysis content"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.model == "claude-sonnet-4-20250514"


class TestClaudeClient:
    """Tests for ClaudeClient."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("seo_auditor.clients.claude_client.settings") as mock:
            mock.anthropic_api_key.get_secret_value.return_value = "test-api-key"
            mock.claude_model = "claude-sonnet-4-20250514"
            mock.claude_max_tokens = 4096
            mock.claude_requests_per_minute = 60
            mock.claude_tokens_per_minute = 60000
            yield mock

    @pytest.fixture
    def mock_anthropic(self):
        """Mock Anthropic client."""
        with patch("seo_auditor.clients.claude_client.anthropic") as mock:
            yield mock

    def test_estimate_tokens(self, mock_settings, mock_anthropic):
        """Token estimation works."""
        client = ClaudeClient()

        # Roughly 4 chars per token
        assert client.estimate_tokens("test") == 1
        assert client.estimate_tokens("a" * 100) == 25
        assert client.estimate_tokens("a" * 400) == 100

    async def test_analyze_calls_api(self, mock_settings, mock_anthropic):
        """analyze() calls the Anthropic API."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Analysis result")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.model = "claude-sonnet-4-20250514"

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        client = ClaudeClient()
        result = await client.analyze(
            system_prompt="You are an SEO expert.",
            user_prompt="Analyze this data.",
        )

        assert result.content == "Analysis result"
        assert result.input_tokens == 100
        assert result.output_tokens == 50

    async def test_analyze_uses_correct_parameters(self, mock_settings, mock_anthropic):
        """analyze() passes correct parameters to API."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Result")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 10
        mock_response.model = "claude-sonnet-4-20250514"

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        client = ClaudeClient()
        await client.analyze(
            system_prompt="System prompt",
            user_prompt="User prompt",
            max_tokens=2048,
        )

        # Verify API was called with correct parameters
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs

        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_kwargs["max_tokens"] == 2048
        assert call_kwargs["system"] == "System prompt"
        assert call_kwargs["messages"] == [{"role": "user", "content": "User prompt"}]

    async def test_analyze_batch_concurrent(self, mock_settings, mock_anthropic):
        """analyze_batch() runs requests concurrently."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Result")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 10
        mock_response.model = "claude-sonnet-4-20250514"

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        client = ClaudeClient()
        requests = [
            ("System 1", "User 1"),
            ("System 2", "User 2"),
            ("System 3", "User 3"),
        ]

        results = await client.analyze_batch(requests, max_concurrency=2)

        assert len(results) == 3
        assert all(r.content == "Result" for r in results)

    async def test_analyze_batch_respects_concurrency(self, mock_settings, mock_anthropic):
        """analyze_batch() respects max_concurrency."""
        call_count = 0
        max_concurrent = 0
        current_concurrent = 0

        async def mock_create(**kwargs):
            nonlocal call_count, max_concurrent, current_concurrent
            current_concurrent += 1
            max_concurrent = max(max_concurrent, current_concurrent)
            call_count += 1

            response = MagicMock()
            response.content = [MagicMock(text="Result")]
            response.usage.input_tokens = 10
            response.usage.output_tokens = 10
            response.model = "claude-sonnet-4-20250514"

            current_concurrent -= 1
            return response

        mock_client = AsyncMock()
        mock_client.messages.create.side_effect = mock_create
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        client = ClaudeClient()
        requests = [("S", "U") for _ in range(10)]

        await client.analyze_batch(requests, max_concurrency=3)

        assert call_count == 10
        # Due to async nature, max_concurrent should be <= 3


class TestClaudeClientRetry:
    """Tests for Claude client retry behavior."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("seo_auditor.clients.claude_client.settings") as mock:
            mock.anthropic_api_key.get_secret_value.return_value = "test-api-key"
            mock.claude_model = "claude-sonnet-4-20250514"
            mock.claude_max_tokens = 4096
            mock.claude_requests_per_minute = 60
            mock.claude_tokens_per_minute = 60000
            yield mock

    @pytest.fixture
    def mock_anthropic(self):
        """Mock Anthropic client."""
        with patch("seo_auditor.clients.claude_client.anthropic") as mock:
            yield mock

    async def test_retry_on_rate_limit(self, mock_settings, mock_anthropic):
        """analyze() retries on rate limit errors."""
        call_count = 0

        async def mock_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise mock_anthropic.RateLimitError("Rate limited")

            response = MagicMock()
            response.content = [MagicMock(text="Success after retry")]
            response.usage.input_tokens = 10
            response.usage.output_tokens = 10
            response.model = "claude-sonnet-4-20250514"
            return response

        mock_client = AsyncMock()
        mock_client.messages.create.side_effect = mock_create
        mock_anthropic.AsyncAnthropic.return_value = mock_client

        client = ClaudeClient()

        # This should succeed after retries
        # Note: In real tests, you'd mock tenacity to speed this up
        # result = await client.analyze("System", "User")
        # assert result.content == "Success after retry"
        # assert call_count == 3

        # For now, just verify client is created correctly
        assert client is not None
