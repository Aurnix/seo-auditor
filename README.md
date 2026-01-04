# SEO Auditor

Automated SEO audits powered by Screaming Frog and Claude AI.

## Features

- **Automated Crawling**: Integrate with Screaming Frog SEO Spider for comprehensive site crawling
- **GSC Integration**: Enrich crawl data with Google Search Console performance metrics (clicks, impressions, CTR, position)
- **AI-Powered Analysis**: Claude AI performs multi-pass analysis across technical, content, links, and performance dimensions
- **Prioritized Action Plans**: Issues are ranked by impact using traffic data and SEO severity
- **Interactive Dashboard**: HTML dashboard with charts, filterable issues, and implementation guidance

## Installation

### Prerequisites

- Python 3.11+
- [Screaming Frog SEO Spider](https://www.screamingfrog.co.uk/seo-spider/) (licensed version for full functionality)
- Anthropic API key

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/seo-auditor.git
cd seo-auditor

# Install with dev dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SEO_AUDITOR_ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `SEO_AUDITOR_GSC_CREDENTIALS_PATH` | No | Path to Google service account JSON |
| `SEO_AUDITOR_GSC_USE_OAUTH` | No | Use OAuth instead of service account |
| `SEO_AUDITOR_SF_EXECUTABLE_PATH` | No | Path to Screaming Frog executable |
| `SEO_AUDITOR_CLAUDE_MODEL` | No | Claude model (default: claude-sonnet-4-20250514) |
| `SEO_AUDITOR_LOG_LEVEL` | No | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Usage

### Basic Audit

```bash
# Run a full SEO audit
seo-audit https://example.com

# Include Google Search Console data
seo-audit https://example.com --gsc "https://example.com/"

# Use existing crawl data (skip crawling)
seo-audit https://example.com --skip-crawl --crawl-path ./crawl_exports/example_20240101/
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--gsc` | GSC property URL for traffic data enrichment |
| `--skip-crawl` | Skip crawling, use existing export |
| `--crawl-path` | Path to existing Screaming Frog export |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │  Screaming Frog     │    │  Google Search Console          │ │
│  │  - URLs & status    │    │  - Clicks & impressions         │ │
│  │  - Titles & metas   │    │  - CTR & avg position           │ │
│  │  - Links & depth    │    │  - Query data                   │ │
│  └──────────┬──────────┘    └───────────────┬─────────────────┘ │
└─────────────┼───────────────────────────────┼───────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED DATA LAYER                            │
│              Merge SF crawl data with GSC metrics                │
│              URL normalization & priority scoring                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CLAUDE ANALYSIS ENGINE                          │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────────────┐  │
│  │ Technical │ │  Content  │ │   Links   │ │   Performance   │  │
│  │   Pass    │ │   Pass    │ │   Pass    │ │      Pass       │  │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └────────┬────────┘  │
│        └─────────────┼─────────────┼────────────────┘           │
│                      ▼                                           │
│              ┌───────────────┐                                   │
│              │  Synthesizer  │ Combine & prioritize findings    │
│              └───────────────┘                                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INTERACTIVE DASHBOARD                          │
│         HTML report with charts, issues, and action plan         │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
seo_auditor/
├── main.py              # CLI entry point and orchestrator
├── config/              # Configuration
│   ├── settings.py      # Pydantic settings with env vars
│   ├── thresholds.py    # SEO threshold configurations
│   ├── logging_config.py
│   └── prompts/         # Markdown prompt templates
│       ├── technical.md
│       ├── content.md
│       ├── links.md
│       ├── performance.md
│       └── synthesis.md
├── auth/                # Authentication
│   └── google_auth.py   # OAuth/service account auth
├── clients/             # External API clients
│   ├── claude_client.py # Rate-limited async Claude client
│   ├── gsc_client.py    # Google Search Console API
│   └── rate_limiter.py  # Token bucket implementation
├── crawler/             # Screaming Frog integration
│   ├── sf_runner.py     # CLI wrapper for SF
│   ├── sf_config.py     # Crawl configuration builder
│   └── exports.py       # Export type definitions
├── ingestion/           # Data parsing
│   ├── sf_parser.py     # Main parser orchestrator
│   ├── merger.py        # Merge SF + GSC data
│   └── parsers/         # Per-export parsers
│       ├── base.py
│       └── internal_html.py
├── analysis/            # Claude analysis
│   ├── passes/          # Analysis pass implementations
│   │   ├── base.py      # Abstract base class
│   │   ├── technical.py
│   │   ├── content.py
│   │   ├── links.py
│   │   └── performance.py
│   ├── chunking.py      # Data chunking for large sites
│   └── synthesizer.py   # Combine passes into report
├── output/              # Report generation
│   ├── renderer.py      # Jinja2 template renderer
│   ├── templates/       # HTML templates
│   └── exporters/       # Export format handlers
├── models/              # Pydantic data models
│   ├── crawl.py         # PageData, CrawlSummary
│   ├── analysis.py      # SEOIssue, AnalysisPassResult
│   ├── report.py        # AuditReport, ExecutiveSummary
│   └── enums.py         # Priority, Effort, IssueCategory
└── utils/               # Utilities
    └── url.py           # URL normalization
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=seo_auditor --cov-report=html

# Run specific test file
pytest tests/test_parsers.py

# Run tests matching pattern
pytest -k "test_claude"

# Verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black seo_auditor tests

# Lint
ruff check seo_auditor

# Type checking
mypy seo_auditor
```

### Adding New Analysis Passes

1. Create a new analyzer in `seo_auditor/analysis/passes/`:

```python
from .base import BaseAnalysisPass
from ...models.enums import AnalysisPassType

class MyAnalyzer(BaseAnalysisPass):
    PASS_TYPE = AnalysisPassType.MY_TYPE
    PROMPT_FILE = "my_pass.md"

    def _get_default_prompt(self) -> str:
        return "Analyze for X. Output JSON with issues array."

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[["url", "relevant_columns"]].copy()
```

2. Add the prompt template in `seo_auditor/config/prompts/my_pass.md`

3. Register the pass in `main.py`

## Analysis Passes

| Pass | Focus Areas | Key Metrics |
|------|-------------|-------------|
| **Technical** | Crawlability, indexability, site architecture | Status codes, robots directives, crawl depth |
| **Content** | On-page SEO elements | Titles, meta descriptions, H1s, word count |
| **Links** | Internal linking structure | Inlinks, outlinks, orphan pages, link equity |
| **Performance** | Speed & Core Web Vitals correlation | Response time, page size, traffic impact |

## Output

The audit generates an HTML dashboard in `./reports/` containing:

- **Health Score**: Overall site health (0-100) with category breakdowns
- **Executive Summary**: Key findings and recommendations
- **Issues List**: All identified issues with priority, effort, and affected URLs
- **Action Plan**: Prioritized tasks ranked by impact and effort
- **Charts**: Visual breakdowns of status codes, indexability, issues by category

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Run linting (`ruff check . && black --check .`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.
