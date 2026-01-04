.PHONY: install dev test lint format typecheck check clean help

# Default target
help:
	@echo "SEO Auditor - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install    Install production dependencies"
	@echo "  make dev        Install dev dependencies + pre-commit hooks"
	@echo ""
	@echo "Quality:"
	@echo "  make test       Run tests with coverage"
	@echo "  make lint       Run ruff linter"
	@echo "  make format     Format code with black"
	@echo "  make typecheck  Run mypy type checker"
	@echo "  make check      Run all checks (lint + typecheck + test)"
	@echo ""
	@echo "Other:"
	@echo "  make clean      Remove build artifacts and cache"

# Setup
install:
	pip install -e .

dev:
	pip install -e ".[dev]"
	pip install pre-commit
	pre-commit install
	@echo "✅ Dev environment ready. Pre-commit hooks installed."

# Quality checks
test:
	pytest --cov=seo_auditor --cov-report=term-missing -v

lint:
	ruff check seo_auditor tests

format:
	black seo_auditor tests
	ruff check --fix seo_auditor tests

typecheck:
	mypy seo_auditor --ignore-missing-imports

check: lint typecheck test
	@echo "✅ All checks passed"

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned build artifacts"
