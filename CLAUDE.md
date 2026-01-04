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

---

## Missing Features & Roadmap

### Priority 1: Core Functionality Gaps

#### Additional Parsers (ingestion/parsers/)
Currently only `internal_html.py` exists. Need to add:

| Parser | Purpose | SF Export File |
|--------|---------|----------------|
| `redirects.py` | Redirect chains, loops, status codes | `redirect_chains.csv` |
| `images.py` | Alt text, file sizes, optimization | `images_missing_alt_text.csv`, `images_over_100kb.csv` |
| `page_titles.py` | Duplicate, missing, length issues | `page_titles_*.csv` |
| `meta_descriptions.py` | Duplicate, missing, length | `meta_descriptions_*.csv` |
| `canonicals.py` | Self-referencing, conflicts | `canonicals.csv` |
| `hreflang.py` | International SEO issues | `hreflang.csv` |
| `structured_data.py` | Schema.org validation | `structured_data.csv` |

#### Enhanced Prompt Templates (config/prompts/)
Current prompts are minimal. Each should include:
- Detailed analysis instructions
- Explicit JSON output schema
- Example outputs
- Edge case handling
- Severity classification criteria

### Priority 2: Export & Output

#### PDF Export (output/exporters/)
The `exporters/` directory is empty. Need:

```python
# output/exporters/pdf.py
class PDFExporter:
    def export(self, report: AuditReport, output_path: Path) -> None:
        # Use weasyprint (already in optional deps)
        pass
```

#### Dashboard Interactivity
Current dashboard is static HTML. Enhancements needed:
- Client-side filtering by category/priority/effort
- Sortable issue tables
- Drill-down into affected URLs
- Export issues to CSV
- Interactive charts (Chart.js or similar)
- Dark mode toggle
- Print-friendly styles

### Priority 3: Additional Analysis Passes

| Pass | Focus | Implementation Notes |
|------|-------|---------------------|
| Images | Alt text, lazy loading, WebP, srcset | Add `IMAGES` to `AnalysisPassType` |
| Structured Data | Schema.org validation, rich snippets | Parse JSON-LD from crawl |
| Mobile | Viewport, tap targets, CLS | Requires JS rendering in SF |
| International | Hreflang, lang attributes | Cross-reference with sitemap |
| Security | HTTPS, mixed content, headers | Parse security.csv from SF |

### Priority 4: Infrastructure & DevOps

#### CI/CD Configuration
```yaml
# .github/workflows/ci.yml
- pytest with coverage reporting
- mypy type checking
- ruff linting
- black formatting check
```

#### Docker Support
```dockerfile
# Dockerfile
FROM python:3.11-slim
# Note: Screaming Frog requires GUI or headless X server
```

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
- black
- ruff
- mypy
- pytest (fast subset)
```

### Priority 5: Advanced Features

| Feature | Description |
|---------|-------------|
| Audit Diffing | Compare two audits, show changes |
| Incremental Crawls | Resume interrupted crawls |
| API Mode | FastAPI wrapper for programmatic access |
| Scheduled Audits | Cron-based recurring audits |
| Slack/Email Alerts | Notify on critical issues |
| Custom Rules Engine | User-defined SEO rules |
| Competitor Analysis | Compare against competitor crawls |

---

## Implementation Path

### Phase 1: Foundation (Quick Wins)
1. Add `.env.example` template file
2. Implement remaining parsers (start with `images.py`, `redirects.py`)
3. Enhance prompt templates with detailed instructions
4. Add PDF exporter using weasyprint

### Phase 2: Dashboard Enhancement
1. Add client-side JavaScript for filtering/sorting
2. Implement Chart.js visualizations
3. Add issue export functionality
4. Improve mobile responsiveness

### Phase 3: Analysis Expansion
1. Add Images analysis pass
2. Add Structured Data analysis pass
3. Implement parallel analysis pass execution
4. Add comparison/diffing between audits

### Phase 4: Production Readiness
1. Add CI/CD pipeline
2. Docker containerization
3. Comprehensive integration tests
4. API mode with FastAPI
5. Documentation site

---

## Known Limitations

1. **Screaming Frog dependency**: Requires licensed SF installation
2. **Single-threaded crawling**: SF CLI doesn't support parallel crawls
3. **No JavaScript rendering by default**: Set `sf_render_javascript: true` in settings
4. **Rate limiting**: Claude API limits may slow large site analysis
5. **Memory usage**: Large crawls (100k+ URLs) may require chunking optimization
