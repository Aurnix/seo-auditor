"""CLI entry point."""
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
import click
from rich.console import Console
from .config.settings import settings
from .config.logging_config import setup_logging, get_logger
from .auth.google_auth import GSCAuthenticator
from .clients.claude_client import ClaudeClient
from .clients.gsc_client import GSCClient, GSCConfig, GSCError
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
    """Orchestrates the SEO audit pipeline."""

    def __init__(
        self,
        claude_client: Optional[ClaudeClient] = None,
        sf_runner: Optional[ScreamingFrogRunner] = None,
        gsc_client: Optional[GSCClient] = None,
    ):
        """Initialize with optional dependency injection for testing."""
        self.claude = claude_client or ClaudeClient()
        self.sf_runner = sf_runner or ScreamingFrogRunner()
        self.sf_parser = SFParser()
        self.merger = DataMerger()
        self.renderer = DashboardRenderer()
        self.gsc_client = gsc_client

        # Auto-initialize GSC client if credentials available and not injected
        if self.gsc_client is None and settings.gsc_credentials_path:
            self._init_gsc_client()

    def _init_gsc_client(self) -> None:
        """Initialize GSC client with proper error handling."""
        try:
            auth = GSCAuthenticator(settings.gsc_credentials_path)
            self.gsc_client = GSCClient(auth.get_service())
            logger.info("GSC client initialized successfully")
        except FileNotFoundError:
            logger.warning(
                "GSC credentials file not found",
                path=str(settings.gsc_credentials_path),
            )
        except ValueError as e:
            logger.warning("GSC authentication failed", error=str(e))
        except Exception as e:
            logger.error(
                "Unexpected error initializing GSC client",
                error_type=type(e).__name__,
                error=str(e),
            )

    async def run_audit(
        self,
        target_url: str,
        gsc_property: str = None,
        skip_crawl: bool = False,
        crawl_path: Path = None,
    ) -> Path:
        """Run a complete SEO audit pipeline."""
        logger.info("Starting SEO audit", target_url=target_url, gsc_property=gsc_property)
        console.print(f"[bold blue]Starting SEO audit for {target_url}[/]")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        settings.ensure_directories()

        # Crawl
        if skip_crawl and crawl_path:
            console.print("Loading existing crawl...")
            logger.info("Loading existing crawl", path=str(crawl_path))
            sf_data = self.sf_parser.parse_export(crawl_path)
        else:
            console.print("Running crawl...")
            logger.info("Starting Screaming Frog crawl")
            export_path = await self.sf_runner.crawl(target_url)
            sf_data = self.sf_parser.parse_export(export_path)

        logger.info("Crawl complete", url_count=len(sf_data))
        console.print(f"   Found {len(sf_data)} URLs")

        # GSC - with graceful degradation
        gsc_data = None
        if self.gsc_client and gsc_property:
            console.print("Fetching GSC data...")
            try:
                gsc_data = self.gsc_client.fetch_page_performance(
                    GSCConfig(site_url=gsc_property)
                )
                logger.info("GSC data fetched", row_count=len(gsc_data) if gsc_data is not None else 0)
            except GSCError as e:
                logger.warning("GSC fetch failed, continuing without GSC data", error=str(e))
                console.print("[yellow]   GSC fetch failed, continuing without GSC data[/]")

        # Merge
        if gsc_data is not None and not gsc_data.empty:
            merged = self.merger.merge(sf_data, gsc_data)
        else:
            merged = sf_data.copy()
            merged["clicks"] = 0
            merged["impressions"] = 0

        # Analyze - run in parallel for efficiency
        console.print("Running Claude analysis...")
        logger.info("Starting analysis passes")

        analyzers = [
            ("technical", TechnicalAnalyzer(self.claude)),
            ("content", ContentAnalyzer(self.claude)),
            ("links", LinksAnalyzer(self.claude)),
            ("performance", PerformanceAnalyzer(self.claude)),
        ]

        async def run_analysis(name: str, analyzer):
            logger.info("Starting analysis pass", pass_name=name)
            console.print(f"   Analyzing {name}...")
            result = await analyzer.analyze(merged)
            logger.info(
                "Analysis pass complete",
                pass_name=name,
                issue_count=len(result.issues),
            )
            return name, result

        # Run all analyses in parallel
        results = await asyncio.gather(
            *[run_analysis(name, analyzer) for name, analyzer in analyzers],
            return_exceptions=True,
        )

        analyses = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error("Analysis pass failed", error=str(result))
            else:
                name, analysis_result = result
                analyses[name] = analysis_result

        # Synthesize
        console.print("Synthesizing report...")
        logger.info("Synthesizing final report")
        synthesizer = Synthesizer(self.claude)
        report = await synthesizer.synthesize(analyses, merged, target_url)

        # Render
        console.print("Generating dashboard...")
        output_path = settings.output_dir / f"audit_{timestamp}.html"
        self.renderer.render(report, output_path)

        logger.info("Audit complete", output_path=str(output_path))
        console.print(f"[bold green]Done! Report: {output_path}[/]")
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
