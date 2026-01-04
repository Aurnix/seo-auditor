"""Token bucket rate limiter."""
import asyncio
import time
from dataclasses import dataclass, field

@dataclass
class TokenBucket:
    capacity: float
    refill_rate: float
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    
    def __post_init__(self):
        self.tokens = self.capacity
        self.last_refill = time.monotonic()
    
    async def acquire(self, tokens: float = 1.0) -> bool:
        async with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            wait_time = (tokens - self.tokens) / self.refill_rate
            await asyncio.sleep(wait_time)
            self._refill()
            self.tokens -= tokens
            return True
    
    def _refill(self):
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.last_refill) * self.refill_rate)
        self.last_refill = now

@dataclass
class DualRateLimiter:
    requests_per_minute: int
    tokens_per_minute: int
    
    def __post_init__(self):
        self.request_bucket = TokenBucket(self.requests_per_minute, self.requests_per_minute / 60.0)
        self.token_bucket = TokenBucket(self.tokens_per_minute, self.tokens_per_minute / 60.0)
    
    async def acquire(self, estimated_tokens: int) -> None:
        await self.request_bucket.acquire(1)
        await self.token_bucket.acquire(estimated_tokens)
