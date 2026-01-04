"""Rate-limited Claude API client."""
import asyncio
from dataclasses import dataclass
from typing import Optional
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ..config.settings import settings
from .rate_limiter import DualRateLimiter

@dataclass
class AnalysisResult:
    content: str
    input_tokens: int
    output_tokens: int
    model: str

class ClaudeClient:
    def __init__(self):
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())
        self._rate_limiter = DualRateLimiter(settings.claude_requests_per_minute, settings.claude_tokens_per_minute)
    
    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
    
    @retry(
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIConnectionError)),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5)
    )
    async def analyze(self, system_prompt: str, user_prompt: str, max_tokens: Optional[int] = None) -> AnalysisResult:
        await self._rate_limiter.acquire(self.estimate_tokens(system_prompt + user_prompt))
        response = await self._client.messages.create(
            model=settings.claude_model,
            max_tokens=max_tokens or settings.claude_max_tokens,
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt
        )
        return AnalysisResult(
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=response.model
        )
    
    async def analyze_batch(self, requests: list[tuple[str, str]], max_concurrency: int = 5) -> list[AnalysisResult]:
        semaphore = asyncio.Semaphore(max_concurrency)
        async def bounded(s, u):
            async with semaphore:
                return await self.analyze(s, u)
        return await asyncio.gather(*[bounded(s, u) for s, u in requests])
