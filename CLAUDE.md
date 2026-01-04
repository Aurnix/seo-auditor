# CLAUDE.md

This file provides guidance for Claude Code when working on this repository.

## Project Overview

SEO Auditor is a Python CLI tool that performs automated SEO audits by integrating Screaming Frog SEO Spider crawl data with Google Search Console metrics, then using Claude AI for multi-pass analysis and generating interactive HTML dashboards.

## Tech Stack

- **Python 3.11+** with async/await patterns
- **Pydantic v2** for data models and settings validation
- **Anthropic SDK** for Claude API integration
- **Click** for CLI interface
- **Rich** for terminal output formatting
- **Pandas** for data processing
- **Jinja2** for HTML template rendering
- **structlog** for structured logging
- **tenacity** for retry logic

## Project Structure

```
seo_auditor/
├── main.py              # CLI entry point and SEOAuditor orchestrator
├── config/              # Settings, thresholds, logging config
│   ├── settings.py      # Pydantic Settings with env vars (SEO_AUDITOR_ prefix)
│   ├── thresholds.py    # SEO threshold configurations
│   └── prompts/         # Markdown prompt templates for each analysis pass
├── auth/                # Google OAuth authentication
├── clients/             # External API clients
│   ├── claude_client.py # Rate-limited async Claude client
│   ├── gsc_client.py    # Google Search Console client
│   └── rate_limiter.py  # Token bucket rate limiter
├── crawler/             # Screaming Frog automation
│   ├── sf_runner.py     # CLI wrapper for SF execution
│   └── sf_config.py     # Crawl configuration
├── ingestion/           # Data parsing and merging
│   ├── sf_parser.py     # Parse SF CSV exports
│   ├── merger.py        # Merge SF + GSC data
│   └── parsers/         # Per-export-type parsers
├── analysis/            # Claude analysis pipeline
│   ├── passes/          # Individual analysis passes (technical, content, links, performance)
│   ├── chunking.py      # Data chunking for large sites
│   └── synthesizer.py   # Combine pass results into final report
├── output/              # Report generation
│   └── renderer.py      # Jinja2 HTML dashboard renderer
└── models/              # Pydantic data models
    ├── crawl.py         # PageData, CrawlSummary, CrawlData
    ├── analysis.py      # Analysis result models
    ├── report.py        # Final report model
    └── enums.py         # Enumerations
```

## Development Commands

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run the CLI
seo-audit https://example.com
seo-audit https://example.com --gsc "https://example.com/"

# Run tests
pytest

# Run tests with coverage
pytest --cov=seo_auditor

# Type checking
mypy seo_auditor

# Linting
ruff check seo_auditor

# Formatting
black seo_auditor tests
```

## Environment Setup

Copy `.env.example` to `.env` and configure:

```bash
# Required
SEO_AUDITOR_ANTHROPIC_API_KEY=sk-ant-...

# Optional - Google Search Console
SEO_AUDITOR_GSC_CREDENTIALS_PATH=./credentials.json
SEO_AUDITOR_GSC_USE_OAUTH=false

# Optional - Screaming Frog path (defaults to macOS location)
SEO_AUDITOR_SF_EXECUTABLE_PATH=/path/to/ScreamingFrogSEOSpider
```

All settings use the `SEO_AUDITOR_` prefix and are defined in `seo_auditor/config/settings.py`.

## Architecture Notes

### Analysis Pipeline

1. **Crawl**: Screaming Frog crawls the target site and exports CSV data
2. **GSC Enrichment**: Optional merge with Google Search Console performance data
3. **Multi-pass Analysis**: Four parallel Claude analysis passes:
   - Technical (status codes, indexability, crawl depth)
   - Content (titles, descriptions, word count)
   - Links (internal linking structure)
   - Performance (Core Web Vitals correlation with traffic)
4. **Synthesis**: Claude combines all pass results into prioritized recommendations
5. **Rendering**: Jinja2 generates the final HTML dashboard

### Key Patterns

- **Async throughout**: All I/O operations use async/await
- **Rate limiting**: Claude client uses token bucket algorithm for API limits
- **Retry logic**: tenacity decorators handle transient API failures
- **Chunking**: Large datasets are chunked before sending to Claude
- **Prompt templates**: Analysis prompts stored as markdown in `config/prompts/`

### Models

- `PageData`: Single URL with all SEO metrics
- `CrawlData`: Collection of pages with summary stats
- `AnalysisResult`: Claude response with token usage tracking

## Testing

Tests are in `tests/` directory. Run with:

```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest tests/test_specific.py   # Run specific test file
pytest -k "test_name"           # Run tests matching pattern
```

Use `pytest-asyncio` for async test functions (configured with `asyncio_mode = "auto"`).

## Code Style

- **Line length**: 100 characters (configured in pyproject.toml)
- **Python version**: 3.11+ (use modern syntax like `list[str]` not `List[str]`)
- **Type hints**: Use throughout, run mypy for validation
- **Formatting**: Black with default settings
- **Linting**: Ruff for fast linting
