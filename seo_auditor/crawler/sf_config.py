"""Screaming Frog configuration."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from ..config.settings import settings

@dataclass
class CrawlConfig:
    start_url: str
    max_urls: int = field(default_factory=lambda: settings.sf_max_urls)
    max_crawl_depth: int = field(default_factory=lambda: settings.sf_max_crawl_depth)
    respect_robots_txt: bool = True
    enable_javascript: bool = False
    user_agent: str = "Googlebot"
    
    def to_config_dict(self) -> dict:
        return {
            "configuration": {
                "spider": {
                    "maxUrlsToSpider": self.max_urls,
                    "maxCrawlDepth": self.max_crawl_depth,
                    "respectRobotsTxt": self.respect_robots_txt,
                },
                "rendering": {"enableJavascript": self.enable_javascript},
                "userAgent": {"preset": self.user_agent},
            }
        }
    
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_config_dict(), f, indent=2)
    
    @classmethod
    def for_full_audit(cls, start_url: str) -> "CrawlConfig":
        return cls(start_url=start_url, max_urls=50000, enable_javascript=True)
