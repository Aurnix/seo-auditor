"""Data merger for SF + GSC."""
import pandas as pd
from ..utils.url import normalize_url

class DataMerger:
    def merge(self, sf_data: pd.DataFrame, gsc_data: pd.DataFrame) -> pd.DataFrame:
        sf_data = sf_data.copy()
        gsc_data = gsc_data.copy()
        
        sf_data["url_normalized"] = sf_data["url"].apply(normalize_url)
        gsc_data["url_normalized"] = gsc_data["page"].apply(normalize_url)
        
        gsc_agg = gsc_data.groupby("url_normalized").agg({
            "clicks": "sum", "impressions": "sum", "ctr": "mean", "position": "mean"
        }).reset_index()
        
        merged = sf_data.merge(gsc_agg, on="url_normalized", how="left")
        
        for col in ["clicks", "impressions"]:
            merged[col] = merged[col].fillna(0).astype(int)
        merged["ctr"] = merged["ctr"].fillna(0)
        merged["avg_position"] = merged.get("position", pd.Series([0])).fillna(0)
        merged["has_traffic"] = merged["clicks"] > 0
        merged["priority_score"] = merged["clicks"].clip(upper=1000) / 10 + merged["impressions"].clip(upper=10000) / 1000
        
        return merged
