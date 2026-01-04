"""Google Search Console client."""
from dataclasses import dataclass
from datetime import date, timedelta
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)


class GSCError(Exception):
    """Base exception for GSC client errors."""

    pass


class GSCAuthError(GSCError):
    """Authentication/authorization error."""

    pass


class GSCQuotaError(GSCError):
    """API quota exceeded."""

    pass


class GSCNotFoundError(GSCError):
    """Site not found or no access."""

    pass


@dataclass
class GSCConfig:
    site_url: str
    days_back: int = 90
    row_limit: int = 25000


class GSCClient:
    """Client for Google Search Console API."""

    def __init__(self, service):
        self._service = service

    def fetch_performance_data(
        self, config: GSCConfig, dimensions: list[str] = None
    ) -> pd.DataFrame:
        """Fetch performance data from GSC.

        Args:
            config: GSC configuration including site URL and date range
            dimensions: Dimensions to group by (default: ["page", "query"])

        Returns:
            DataFrame with performance metrics

        Raises:
            GSCAuthError: If authentication fails or token is expired
            GSCQuotaError: If API quota is exceeded
            GSCNotFoundError: If site is not found or user lacks access
            GSCError: For other API errors
        """
        dimensions = dimensions or ["page", "query"]
        end_date = date.today() - timedelta(days=3)
        start_date = end_date - timedelta(days=config.days_back)

        request = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": dimensions,
            "rowLimit": config.row_limit,
        }

        logger.info(
            "Fetching GSC performance data",
            site_url=config.site_url,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            dimensions=dimensions,
        )

        try:
            response = (
                self._service.searchanalytics()
                .query(siteUrl=config.site_url, body=request)
                .execute()
            )
        except Exception as e:
            self._handle_api_error(e, config.site_url)

        rows = response.get("rows", [])
        logger.info("GSC data received", row_count=len(rows))

        if not rows:
            return pd.DataFrame()

        data = []
        for row in rows:
            keys = row.get("keys", [])
            record = {
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": row.get("ctr", 0),
                "position": row.get("position", 0),
            }
            for i, dim in enumerate(dimensions):
                record[dim] = keys[i] if i < len(keys) else None
            data.append(record)

        return pd.DataFrame(data)

    def fetch_page_performance(self, config: GSCConfig) -> pd.DataFrame:
        """Fetch page-level performance data."""
        return self.fetch_performance_data(config, dimensions=["page"])

    def _handle_api_error(self, error: Exception, site_url: str) -> None:
        """Convert Google API errors to typed exceptions."""
        error_str = str(error).lower()

        # Check for common error patterns
        if "invalid_grant" in error_str or "token" in error_str:
            logger.error("GSC authentication failed", site_url=site_url, error=str(error))
            raise GSCAuthError(f"Authentication failed: {error}") from error

        if "quota" in error_str or "rateLimitExceeded" in error_str:
            logger.error("GSC quota exceeded", site_url=site_url, error=str(error))
            raise GSCQuotaError(f"API quota exceeded: {error}") from error

        if "403" in error_str or "forbidden" in error_str:
            logger.error("GSC access denied", site_url=site_url, error=str(error))
            raise GSCNotFoundError(f"Access denied for site: {site_url}") from error

        if "404" in error_str or "not found" in error_str:
            logger.error("GSC site not found", site_url=site_url, error=str(error))
            raise GSCNotFoundError(f"Site not found: {site_url}") from error

        # Generic error
        logger.error("GSC API error", site_url=site_url, error=str(error))
        raise GSCError(f"GSC API error: {error}") from error
