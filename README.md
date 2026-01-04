# SEO Auditor

Automated SEO audits powered by Screaming Frog and Claude AI.

## Features

- **Automated Crawling**: Integrate with Screaming Frog SEO Spider
- **GSC Integration**: Enrich crawl data with search performance metrics
- **AI-Powered Analysis**: Claude analyzes data and provides actionable insights
- **Interactive Dashboard**: HTML dashboard with charts and recommendations

## Installation

```bash
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your API keys
```

## Usage

```bash
seo-audit https://example.com
seo-audit https://example.com --gsc "https://example.com/"
```

## Architecture

```
DATA SOURCES (Screaming Frog + GSC)
         ↓
UNIFIED DATA LAYER (Merge & Enrich)
         ↓
CLAUDE ANALYSIS ENGINE (Multi-pass)
         ↓
INTERACTIVE DASHBOARD (HTML Report)
```

## Project Structure

```
seo_auditor/
├── config/          # Settings, thresholds, prompts
├── auth/            # API authentication
├── clients/         # Claude and GSC clients
├── crawler/         # Screaming Frog automation
├── ingestion/       # Data parsing
├── analysis/        # Claude analysis passes
├── output/          # Dashboard generation
├── models/          # Pydantic models
└── utils/           # Utilities
```
