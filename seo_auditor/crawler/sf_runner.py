"""Screaming Frog CLI runner."""
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
import platform
from ..config.settings import settings
from ..config.logging_config import get_logger
from .sf_config import CrawlConfig
from .exports import DEFAULT_EXPORTS

logger = get_logger(__name__)

class ScreamingFrogError(Exception):
    pass

class ScreamingFrogRunner:
    def __init__(self):
        self.executable = settings.sf_executable_path
        self.memory = settings.sf_memory_allocation
        self.timeout_minutes = settings.sf_crawl_timeout_minutes
    
    async def crawl(self, url: str, config: Optional[CrawlConfig] = None, output_dir: Optional[Path] = None) -> Path:
        config = config or CrawlConfig.for_full_audit(url)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        
        if output_dir is None:
            output_dir = settings.crawl_export_dir / f"{domain}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = output_dir / "crawl_config.seospiderconfig"
        config.save(config_path)
        
        logger.info("starting_crawl", url=url, output_dir=str(output_dir))
        
        cmd = [str(self.executable), "--crawl", url, "--config", str(config_path),
               "--headless", "--output-folder", str(output_dir), "--export-format", "csv",
               "--max-memory", self.memory]
        
        for export in DEFAULT_EXPORTS:
            cmd.extend(["--export-tabs", export.export_type.value])
        
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        
        try:
            await asyncio.wait_for(process.communicate(), timeout=self.timeout_minutes * 60)
            if process.returncode != 0:
                raise ScreamingFrogError("Crawl failed")
        except asyncio.TimeoutError:
            process.kill()
            raise ScreamingFrogError(f"Crawl timed out after {self.timeout_minutes} minutes")
        
        logger.info("crawl_completed", output_dir=str(output_dir))
        return output_dir
