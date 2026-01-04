"""Google Search Console client."""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
import pandas as pd

@dataclass
class GSCConfig:
    site_url: str
    days_back: int = 90
    row_limit: int = 25000

class GSCClient:
    def __init__(self, service):
        self._service = service
    
    def fetch_performance_data(self, config: GSCConfig, dimensions: list[str] = None) -> pd.DataFrame:
        dimensions = dimensions or ["page", "query"]
        end_date = date.today() - timedelta(days=3)
        start_date = end_date - timedelta(days=config.days_back)
        
        request = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": dimensions,
            "rowLimit": config.row_limit,
        }
        
        response = self._service.searchanalytics().query(siteUrl=config.site_url, body=request).execute()
        rows = response.get("rows", [])
        
        if not rows:
            return pd.DataFrame()
        
        data = []
        for row in rows:
            keys = row.get("keys", [])
            record = {"clicks": row.get("clicks", 0), "impressions": row.get("impressions", 0),
                      "ctr": row.get("ctr", 0), "position": row.get("position", 0)}
            for i, dim in enumerate(dimensions):
                record[dim] = keys[i] if i < len(keys) else None
            data.append(record)
        return pd.DataFrame(data)
    
    def fetch_page_performance(self, config: GSCConfig) -> pd.DataFrame:
        return self.fetch_performance_data(config, dimensions=["page"])
