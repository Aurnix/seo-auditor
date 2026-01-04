"""Tests for rate limiter."""
import asyncio
import time
import pytest
from seo_auditor.clients.rate_limiter import TokenBucket, DualRateLimiter


class TestTokenBucket:
    """Tests for TokenBucket rate limiter."""

    @pytest.fixture
    def bucket(self):
        """Create a bucket with 10 capacity, 10 tokens/second refill."""
        return TokenBucket(capacity=10.0, refill_rate=10.0)

    async def test_acquire_single_token(self, bucket):
        """Acquiring a single token works."""
        result = await bucket.acquire(1.0)
        assert result is True
        assert bucket.tokens == 9.0

    async def test_acquire_multiple_tokens(self, bucket):
        """Acquiring multiple tokens works."""
        result = await bucket.acquire(5.0)
        assert result is True
        assert bucket.tokens == 5.0

    async def test_acquire_all_tokens(self, bucket):
        """Acquiring all tokens works."""
        result = await bucket.acquire(10.0)
        assert result is True
        assert bucket.tokens == 0.0

    async def test_acquire_waits_when_insufficient(self):
        """Acquiring more tokens than available waits for refill."""
        bucket = TokenBucket(capacity=10.0, refill_rate=100.0)  # Fast refill
        await bucket.acquire(10.0)  # Drain bucket

        start = time.monotonic()
        await bucket.acquire(1.0)  # Should wait briefly
        elapsed = time.monotonic() - start

        # With 100 tokens/sec refill, waiting for 1 token takes ~0.01s
        assert elapsed < 0.5  # Should be fast with high refill rate

    async def test_refill_over_time(self):
        """Tokens refill over time."""
        bucket = TokenBucket(capacity=10.0, refill_rate=1000.0)  # Very fast
        await bucket.acquire(10.0)
        await asyncio.sleep(0.02)  # Wait for refill

        # Should have some tokens back
        bucket._refill()
        assert bucket.tokens > 0

    async def test_capacity_not_exceeded(self):
        """Refill doesn't exceed capacity."""
        bucket = TokenBucket(capacity=10.0, refill_rate=1000.0)
        await asyncio.sleep(0.1)  # Wait longer than needed
        bucket._refill()

        assert bucket.tokens <= bucket.capacity


class TestDualRateLimiter:
    """Tests for DualRateLimiter."""

    @pytest.fixture
    def limiter(self):
        """Create a dual limiter."""
        return DualRateLimiter(requests_per_minute=60, tokens_per_minute=60000)

    async def test_acquire_checks_both_buckets(self, limiter):
        """Acquire consumes from both buckets."""
        await limiter.acquire(100)

        # Request bucket should have 1 fewer request
        assert limiter.request_bucket.tokens < 60
        # Token bucket should have fewer tokens
        assert limiter.token_bucket.tokens < 60000

    async def test_multiple_acquires(self, limiter):
        """Multiple acquires work correctly."""
        for _ in range(3):
            await limiter.acquire(100)

        assert limiter.request_bucket.tokens < 58

    async def test_limiter_initialization(self, limiter):
        """Limiter initializes correctly."""
        assert limiter.requests_per_minute == 60
        assert limiter.tokens_per_minute == 60000
        assert limiter.request_bucket.capacity == 60
        assert limiter.token_bucket.capacity == 60000
