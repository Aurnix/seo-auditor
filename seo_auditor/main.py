"""CLI entry point."""
import asyncio
from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
from .config.settings import settings
from .config.logging_config import setup_logging, get_logger
from .auth.google_auth import GSCAuthenticator
from .clients.claude_client import ClaudeClient
from .clients.gsc_client import GSCClient, GSCConfig
from .crawler.sf_runner import ScreamingFrogRunner
from .ingestion.sf_parser import SFParser
from .ingestion.merger import DataMerger
from .analysis.passes.technical import TechnicalAnalyzer
from .analysis.passes.content import ContentAnalyzer
from .analysis.passes.links import LinksAnalyzer
from .analysis.passes.performance import PerformanceAnalyzer
from .analysis.synthesizer import Synthesizer
from .output.renderer import DashboardRenderer

console = Console()
logger = get_logger(__name__)

class SEOAuditor:
    def __init__(self):
        self.claude = ClaudeClient()
        self.sf_runner = ScreamingFrogRunner()
        self.sf_parser = SFParser()
        self.merger = DataMerger()
        self.renderer = DashboardRenderer()
        self.gsc_client = None
        
        if settings.gsc_credentials_path:
            try:
                auth = GSCAuthenticator(settings.gsc_credentials_path)
                self.gsc_client = GSCClient(auth.get_service())
            except: pass
    
    async def run_audit(self, target_url: str, gsc_property: str = None,
                        skip_crawl: bool = False, crawl_path: Path = None) -> Path:
        console.print(f"[bold blue]🔍 Starting SEO audit for {target_url}[/]")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        settings.ensure_directories()
        
        # Crawl
        if skip_crawl and crawl_path:
            console.print("📂 Loading existing crawl...")
            sf_data = self.sf_parser.parse_export(crawl_path)
        else:
            console.print("🕷️ Running crawl...")
            export_path = await self.sf_runner.crawl(target_url)
            sf_data = self.sf_parser.parse_export(export_path)
        
        console.print(f"   Found {len(sf_data)} URLs")
        
        # GSC
        gsc_data = None
        if self.gsc_client and gsc_property:
            console.print("📊 Fetching GSC data...")
            gsc_data = self.gsc_client.fetch_page_performance(GSCConfig(site_url=gsc_property))
        
        # Merge
        if gsc_data is not None and not gsc_data.empty:
            merged = self.merger.merge(sf_data, gsc_data)
        else:
            merged = sf_data
            merged["clicks"] = 0
            merged["impressions"] = 0
        
        # Analyze
        console.print("🤖 Running Claude analysis...")
        analyses = {}
        for name, analyzer in [("technical", TechnicalAnalyzer(self.claude)),
                                ("content", ContentAnalyzer(self.claude)),
                                ("links", LinksAnalyzer(self.claude)),
                                ("performance", PerformanceAnalyzer(self.claude))]:
            console.print(f"   Analyzing {name}...")
            analyses[name] = await analyzer.analyze(merged)
        
        # Synthesize
        console.print("📝 Synthesizing...")
        synthesizer = Synthesizer(self.claude)
        report = await synthesizer.synthesize(analyses, merged, target_url)
        
        # Render
        console.print("🎨 Generating dashboard...")
        output_path = settings.output_dir / f"audit_{timestamp}.html"
        self.renderer.render(report, output_path)
        
        console.print(f"[bold green]✅ Done! Report: {output_path}[/]")
        return output_path

@click.command()
@click.argument("url")
@click.option("--gsc", default=None, help="GSC property URL")
@click.option("--skip-crawl", is_flag=True, help="Skip crawl")
@click.option("--crawl-path", type=Path, default=None, help="Existing crawl path")
def cli(url: str, gsc: str, skip_crawl: bool, crawl_path: Path):
    """Run SEO audit on URL."""
    setup_logging()
    auditor = SEOAuditor()
    asyncio.run(auditor.run_audit(url, gsc, skip_crawl, crawl_path))

if __name__ == "__main__":
    cli()
