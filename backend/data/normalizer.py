"""
Data Normalizer — Unified Cost Taxonomy
Normalizes raw billing data from all providers into a canonical schema.
"""

import pandas as pd
import numpy as np


CATEGORY_MAP = {
    # AWS
    "EC2": "compute", "EKS": "compute", "Lambda": "compute",
    "S3": "storage",
    "RDS": "database",
    "CloudFront": "networking", "DataTransfer": "networking",
    "Glue": "analytics",
    # Azure
    "VirtualMachines": "compute", "AKS": "compute", "AzureFunctions": "compute",
    "BlobStorage": "storage",
    "CosmosDB": "database",
    "CDN": "networking", "BandwidthOut": "networking",
    "Databricks": "analytics",
    # GCP
    "ComputeEngine": "compute", "GKE": "compute", "CloudFunctions": "compute",
    "CloudStorage": "storage",
    "CloudSQL": "database",
    "CloudCDN": "networking", "EgressCost": "networking",
    "BigQuery": "analytics",
}

PROVIDER_DISPLAY = {
    "aws": "Amazon Web Services",
    "azure": "Microsoft Azure",
    "gcp": "Google Cloud Platform",
}


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Apply unified taxonomy and enrichments."""
    df = df.copy()

    # Ensure category is set from map if missing
    if "category" not in df.columns:
        df["category"] = df["service"].map(CATEGORY_MAP).fillna("other")

    df["provider_display"] = df["provider"].map(PROVIDER_DISPLAY)

    # Month bucket for aggregation
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day

    # Unified resource key
    df["resource_key"] = (
        df["provider"] + "/" + df["service"] + "/" +
        df["team"] + "/" + df["environment"]
    )

    return df


def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Daily spend per resource_key — used by anomaly detection."""
    # Group by resource_key (aggregates across regions), track anomaly status
    agg = df.groupby(["date", "provider", "service", "category", "team", "environment", "resource_key"]).agg(
        cost_usd=("cost_usd", "sum"),
        is_anomaly=("is_anomaly", "max"),
        anomaly_id=("anomaly_id", lambda x: x.dropna().iloc[0] if x.dropna().any() else None),
    ).reset_index()
    return agg


def aggregate_by_provider_service(df: pd.DataFrame) -> pd.DataFrame:
    """Daily spend per provider+service — for multi-cloud overview."""
    return (
        df.groupby(["date", "provider", "service", "category"])
        ["cost_usd"].sum()
        .reset_index()
    )


def aggregate_by_team(df: pd.DataFrame) -> pd.DataFrame:
    """Daily spend per team — for budget tracking."""
    return (
        df.groupby(["date", "team", "environment"])
        ["cost_usd"].sum()
        .reset_index()
    )


def get_summary_stats(df: pd.DataFrame) -> dict:
    """High-level summary statistics for KPI cards."""
    total_spend = df["cost_usd"].sum()
    last_30 = df[df["date"] >= df["date"].max() - pd.Timedelta(days=30)]
    prev_30 = df[
        (df["date"] >= df["date"].max() - pd.Timedelta(days=60)) &
        (df["date"] < df["date"].max() - pd.Timedelta(days=30))
    ]

    mom_change = 0.0
    if prev_30["cost_usd"].sum() > 0:
        mom_change = ((last_30["cost_usd"].sum() - prev_30["cost_usd"].sum()) /
                      prev_30["cost_usd"].sum()) * 100

    return {
        "total_spend_6m": round(total_spend, 2),
        "spend_last_30d": round(last_30["cost_usd"].sum(), 2),
        "mom_change_pct": round(mom_change, 2),
        "providers_count": df["provider"].nunique(),
        "services_count": df["service"].nunique(),
        "teams_count": df["team"].nunique(),
        "anomaly_count": df[df["is_anomaly"] == 1]["anomaly_id"].nunique(),
    }
