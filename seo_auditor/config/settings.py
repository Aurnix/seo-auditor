"""Application settings with environment variable loading."""
from pathlib import Path
from typing import Optional, Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_prefix="SEO_AUDITOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Claude API
    anthropic_api_key: SecretStr = Field(..., description="Anthropic API key")
    claude_model: str = Field(default="claude-sonnet-4-20250514")
    claude_max_tokens: int = Field(default=8192, ge=1, le=16384)
    claude_requests_per_minute: int = Field(default=50, ge=1)
    claude_tokens_per_minute: int = Field(default=80000, ge=1000)
    claude_max_retries: int = Field(default=5, ge=1)
    claude_timeout_seconds: int = Field(default=120, ge=30)
    
    # Google Search Console
    gsc_credentials_path: Optional[Path] = Field(default=None)
    gsc_use_oauth: bool = Field(default=False)
    gsc_oauth_credentials_path: Optional[Path] = Field(default=None)
    gsc_days_back: int = Field(default=90, ge=1, le=365)
    gsc_row_limit: int = Field(default=25000, ge=100)
    
    # Screaming Frog
    sf_executable_path: Path = Field(
        default=Path("/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher")
    )
    sf_memory_allocation: str = Field(default="4g", pattern=r"^\d+[gGmM]$")
    sf_max_crawl_depth: int = Field(default=10, ge=1)
    sf_max_urls: int = Field(default=50000, ge=100)
    sf_crawl_timeout_minutes: int = Field(default=120, ge=10)
    sf_respect_robots: bool = Field(default=True)
    sf_render_javascript: bool = Field(default=False)
    sf_user_agent: str = Field(default="Googlebot")
    
    # Output
    output_dir: Path = Field(default=Path("./reports"))
    crawl_export_dir: Path = Field(default=Path("./crawl_exports"))
    
    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_format: Literal["json", "console"] = Field(default="console")
    log_file: Optional[Path] = Field(default=None)
    
    # Analysis
    max_urls_per_chunk: int = Field(default=500, ge=50)
    max_concurrent_analyses: int = Field(default=3, ge=1)
    
    def ensure_directories(self) -> None:
        """Create required directories."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.crawl_export_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
