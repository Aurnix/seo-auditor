"""Tests for Pydantic models."""
from datetime import datetime
import pytest
from seo_auditor.models.crawl import PageData, CrawlSummary, CrawlData
from seo_auditor.models.analysis import (
    AffectedURL,
    SEOIssue,
    AnalysisPassResult,
    ActionItem,
)
from seo_auditor.models.report import (
    HealthScore,
    ExecutiveSummary,
    IssuesByCategory,
    ChartData,
    AuditReport,
)
from seo_auditor.models.enums import Priority, Effort, IssueCategory, AnalysisPassType


class TestPageData:
    """Tests for PageData model."""

    def test_page_data_defaults(self):
        """PageData has sensible defaults."""
        page = PageData(url="https://example.com/page")

        assert page.url == "https://example.com/page"
        assert page.status_code == 0
        assert page.indexability == "indexable"
        assert page.clicks == 0
        assert page.impressions == 0

    def test_page_data_with_values(self):
        """PageData accepts all values."""
        page = PageData(
            url="https://example.com",
            status_code=200,
            title="Test Page",
            meta_description="Description",
            h1="Main Heading",
            word_count=500,
            clicks=100,
            impressions=1000,
        )

        assert page.status_code == 200
        assert page.title == "Test Page"
        assert page.clicks == 100

    def test_page_data_extra_fields_allowed(self):
        """PageData allows extra fields."""
        page = PageData(
            url="https://example.com",
            custom_field="custom_value",
        )

        assert page.custom_field == "custom_value"


class TestCrawlSummary:
    """Tests for CrawlSummary model."""

    def test_crawl_summary_defaults(self):
        """CrawlSummary has zero defaults."""
        summary = CrawlSummary()

        assert summary.total_urls == 0
        assert summary.status_2xx == 0
        assert summary.missing_title == 0

    def test_crawl_summary_with_values(self):
        """CrawlSummary accepts values."""
        summary = CrawlSummary(
            total_urls=1000,
            status_2xx=900,
            status_4xx=50,
            missing_title=10,
        )

        assert summary.total_urls == 1000
        assert summary.status_2xx == 900


class TestCrawlData:
    """Tests for CrawlData model."""

    def test_crawl_data_with_pages(self):
        """CrawlData contains pages."""
        pages = [
            PageData(url="https://example.com/1"),
            PageData(url="https://example.com/2"),
        ]
        data = CrawlData(site_url="https://example.com", pages=pages)

        assert len(data.pages) == 2
        assert data.site_url == "https://example.com"

    def test_crawl_data_auto_timestamp(self):
        """CrawlData auto-generates timestamp."""
        data = CrawlData(site_url="https://example.com")

        assert isinstance(data.crawl_date, datetime)


class TestSEOIssue:
    """Tests for SEOIssue model."""

    @pytest.fixture
    def issue(self):
        return SEOIssue(
            id="tech_001",
            category=IssueCategory.TECHNICAL,
            title="Missing Title Tags",
            description="50 pages are missing title tags",
            impact="Title tags are critical for SEO",
            priority=Priority.HIGH,
            effort=Effort.QUICK_WIN,
            affected_count=50,
            recommendation="Add unique title tags to all pages",
            total_affected_clicks=500,
        )

    def test_issue_creation(self, issue):
        """Issue is created correctly."""
        assert issue.id == "tech_001"
        assert issue.category == IssueCategory.TECHNICAL
        assert issue.priority == Priority.HIGH

    def test_issue_impact_score_calculation(self, issue):
        """Impact score is calculated correctly."""
        # HIGH priority = 3, clicks = 500
        # Formula: 3 * (1 + min(500/100, 2.0)) = 3 * 3 = 9
        assert issue.impact_score == 9.0

    def test_issue_impact_score_caps_clicks(self):
        """Impact score caps click multiplier at 2."""
        issue = SEOIssue(
            id="test",
            category=IssueCategory.CONTENT,
            title="Test",
            description="Test",
            impact="Test",
            priority=Priority.CRITICAL,
            effort=Effort.MODERATE,
            recommendation="Test",
            total_affected_clicks=10000,  # Very high
        )

        # CRITICAL = 4, capped multiplier = 3 (1 + 2.0)
        assert issue.impact_score == 12.0

    def test_issue_with_affected_urls(self):
        """Issue contains affected URLs."""
        issue = SEOIssue(
            id="test",
            category=IssueCategory.TECHNICAL,
            title="Test",
            description="Test",
            impact="Test",
            priority=Priority.MEDIUM,
            effort=Effort.MODERATE,
            recommendation="Test",
            affected_urls=[
                AffectedURL(url="https://example.com/1", clicks=10),
                AffectedURL(url="https://example.com/2", clicks=20),
            ],
        )

        assert len(issue.affected_urls) == 2
        assert issue.affected_urls[0].clicks == 10


class TestAnalysisPassResult:
    """Tests for AnalysisPassResult model."""

    def test_pass_result_defaults(self):
        """AnalysisPassResult has defaults."""
        result = AnalysisPassResult(pass_type=AnalysisPassType.TECHNICAL)

        assert result.pass_type == AnalysisPassType.TECHNICAL
        assert result.issues == []
        assert result.input_tokens == 0

    def test_pass_result_with_issues(self):
        """AnalysisPassResult contains issues."""
        issues = [
            SEOIssue(
                id="test",
                category=IssueCategory.TECHNICAL,
                title="Test",
                description="Test",
                impact="Test",
                priority=Priority.LOW,
                effort=Effort.QUICK_WIN,
                recommendation="Test",
            )
        ]
        result = AnalysisPassResult(
            pass_type=AnalysisPassType.TECHNICAL,
            issues=issues,
            summary="Found 1 issue",
            input_tokens=1000,
            output_tokens=500,
        )

        assert len(result.issues) == 1
        assert result.input_tokens == 1000


class TestHealthScore:
    """Tests for HealthScore model."""

    def test_health_score_validation(self):
        """HealthScore validates range."""
        score = HealthScore(overall=75)
        assert score.overall == 75

    def test_health_score_range_error(self):
        """HealthScore rejects invalid values."""
        with pytest.raises(ValueError):
            HealthScore(overall=150)

        with pytest.raises(ValueError):
            HealthScore(overall=-10)


class TestIssuesByCategory:
    """Tests for IssuesByCategory model."""

    def test_total_count_empty(self):
        """total_count returns 0 for empty categories."""
        issues = IssuesByCategory()
        assert issues.total_count == 0

    def test_total_count_with_issues(self):
        """total_count sums all categories."""
        issue = SEOIssue(
            id="test",
            category=IssueCategory.TECHNICAL,
            title="Test",
            description="Test",
            impact="Test",
            priority=Priority.LOW,
            effort=Effort.QUICK_WIN,
            recommendation="Test",
        )
        issues = IssuesByCategory(
            technical=[issue, issue],
            content=[issue],
            links=[issue, issue, issue],
        )

        assert issues.total_count == 6


class TestAuditReport:
    """Tests for AuditReport model."""

    def test_audit_report_creation(self):
        """AuditReport is created correctly."""
        report = AuditReport(
            report_id="report_123",
            site_url="https://example.com",
            health_score=HealthScore(overall=75, technical=80, content=70, links=75),
            executive_summary=ExecutiveSummary(
                headline="Site needs improvement",
                key_findings=["Missing titles", "Slow pages"],
            ),
            crawl_summary=CrawlSummary(total_urls=1000),
            crawl_date=datetime.now(),
            issues=IssuesByCategory(),
        )

        assert report.report_id == "report_123"
        assert report.health_score.overall == 75
        assert len(report.executive_summary.key_findings) == 2
