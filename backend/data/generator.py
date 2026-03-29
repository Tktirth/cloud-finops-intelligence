"""
Synthetic Multi-Cloud Billing Data Generator
Generates 6 months of realistic billing data for AWS, Azure, and GCP
with injected labeled anomalies for model training and evaluation.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import json
import os
from zoneinfo import ZoneInfo

np.random.seed(42)
random.seed(42)

# ─────────────────────────────────────────────
# Cloud Provider Configurations
# ─────────────────────────────────────────────

PROVIDERS = {
    "aws": {
        "services": {
            "EC2": {"base_cost": 4200, "category": "compute"},
            "S3": {"base_cost": 820, "category": "storage"},
            "RDS": {"base_cost": 1600, "category": "database"},
            "Lambda": {"base_cost": 140, "category": "compute"},
            "CloudFront": {"base_cost": 320, "category": "networking"},
            "EKS": {"base_cost": 1100, "category": "compute"},
            "DataTransfer": {"base_cost": 560, "category": "networking"},
            "Glue": {"base_cost": 380, "category": "analytics"},
        }
    },
    "azure": {
        "services": {
            "VirtualMachines": {"base_cost": 3800, "category": "compute"},
            "BlobStorage": {"base_cost": 680, "category": "storage"},
            "CosmosDB": {"base_cost": 1200, "category": "database"},
            "AzureFunctions": {"base_cost": 110, "category": "compute"},
            "CDN": {"base_cost": 240, "category": "networking"},
            "AKS": {"base_cost": 950, "category": "compute"},
            "BandwidthOut": {"base_cost": 430, "category": "networking"},
            "Databricks": {"base_cost": 620, "category": "analytics"},
        }
    },
    "gcp": {
        "services": {
            "ComputeEngine": {"base_cost": 3500, "category": "compute"},
            "CloudStorage": {"base_cost": 590, "category": "storage"},
            "CloudSQL": {"base_cost": 1050, "category": "database"},
            "CloudFunctions": {"base_cost": 95, "category": "compute"},
            "CloudCDN": {"base_cost": 200, "category": "networking"},
            "GKE": {"base_cost": 870, "category": "compute"},
            "EgressCost": {"base_cost": 390, "category": "networking"},
            "BigQuery": {"base_cost": 750, "category": "analytics"},
        }
    }
}

TEAMS = ["platform", "data-engineering", "ml-ops", "frontend", "devops"]
ENVS = ["production", "staging", "development"]

TEAM_WEIGHTS = {"platform": 0.30, "data-engineering": 0.25, "ml-ops": 0.20, "frontend": 0.15, "devops": 0.10}
ENV_WEIGHTS = {"production": 0.65, "staging": 0.25, "development": 0.10}

REGIONS = {
    "aws": ["us-east-1", "us-west-2", "eu-west-1"],
    "azure": ["eastus", "westeurope", "southeastasia"],
    "gcp": ["us-central1", "europe-west1", "asia-east1"],
}

# ─────────────────────────────────────────────
# Anomaly Injection Definitions
# ─────────────────────────────────────────────

ANOMALY_EVENTS = [
    {
        "id": "A001",
        "type": "sudden_spike",
        "description": "Auto-scaling group runaway triggered by health check loop",
        "provider": "aws",
        "service": "EC2",
        "team": "platform",
        "env": "production",
        "start_day": 45,
        "duration_days": 3,
        "multiplier": 4.2,
        "root_cause": "Misconfigured ALB health check caused continuous instance replacement",
        "contributing_services": ["EC2", "DataTransfer"],
    },
    {
        "id": "A002",
        "type": "gradual_drift",
        "description": "Storage cost creep due to unmanaged snapshot accumulation",
        "provider": "gcp",
        "service": "CloudStorage",
        "team": "data-engineering",
        "env": "production",
        "start_day": 80,
        "duration_days": 40,
        "drift_per_day": 0.025,
        "root_cause": "Automated ML experiment snapshots without TTL policy",
        "contributing_services": ["CloudStorage", "BigQuery"],
    },
    {
        "id": "A003",
        "type": "data_transfer_blast",
        "description": "Massive data transfer spike from misconfigured cross-region backup",
        "provider": "azure",
        "service": "BandwidthOut",
        "team": "devops",
        "env": "production",
        "start_day": 120,
        "duration_days": 2,
        "multiplier": 8.5,
        "root_cause": "Backup job misconfigured to replicate to wrong region repeatedly",
        "contributing_services": ["BandwidthOut", "BlobStorage"],
    },
    {
        "id": "A004",
        "type": "correlated_spike",
        "description": "Correlated compute and network cost surge during data migration",
        "provider": "aws",
        "service": "EC2",
        "team": "data-engineering",
        "env": "production",
        "start_day": 155,
        "duration_days": 5,
        "multiplier": 2.8,
        "root_cause": "Unplanned database migration ran during business hours with auto-retry",
        "contributing_services": ["EC2", "DataTransfer", "RDS"],
    },
    {
        "id": "A005",
        "type": "seasonal_deviation",
        "description": "GPU compute cost anomaly during off-hours model training batch",
        "provider": "gcp",
        "service": "ComputeEngine",
        "team": "ml-ops",
        "env": "staging",
        "start_day": 100,
        "duration_days": 7,
        "multiplier": 3.1,
        "root_cause": "Cron job schedule drift caused training batch to overlap with peak pricing window",
        "contributing_services": ["ComputeEngine", "EgressCost"],
    },
]


def _weekly_pattern(day_of_week: int) -> float:
    """Business day multiplier (Mon-Fri higher, weekends lower)."""
    patterns = [1.05, 1.10, 1.08, 1.07, 1.06, 0.72, 0.68]
    return patterns[day_of_week]


def _monthly_pattern(day_of_month: int) -> float:
    """Slight cost bump at end-of-month billing cycles."""
    if day_of_month >= 28:
        return 1.04
    elif day_of_month <= 3:
        return 1.02
    return 1.0


def _growth_trend(day_idx: int, total_days: int) -> float:
    """Simulate 20% annual growth → ~10% over 6 months."""
    return 1.0 + 0.10 * (day_idx / total_days)


def get_anomaly_multiplier(provider: str, service: str, team: str, env: str, day_idx: int) -> tuple:
    """Return (multiplier, anomaly_id) for a given record if an anomaly applies."""
    for ev in ANOMALY_EVENTS:
        if (ev["provider"] == provider and
                ev["service"] == service and
                ev["team"] == team and
                ev["env"] == env):
            start = ev["start_day"]
            end = start + ev["duration_days"]
            if start <= day_idx < end:
                if ev["type"] == "gradual_drift":
                    drift = 1.0 + ev["drift_per_day"] * (day_idx - start)
                    return min(drift, 3.0), ev["id"]
                else:
                    return ev["multiplier"], ev["id"]
    return 1.0, None


def generate_billing_data(days: int = 180) -> pd.DataFrame:
    """Generate unified billing DataFrame for all providers."""
    start_date = datetime.now(ZoneInfo('Asia/Kolkata')) - timedelta(days=days)
    records = []

    for day_idx in range(days):
        date = start_date + timedelta(days=day_idx)
        dow = date.weekday()
        dom = date.day

        weekly_m = _weekly_pattern(dow)
        monthly_m = _monthly_pattern(dom)
        growth_m = _growth_trend(day_idx, days)

        for provider, pconfig in PROVIDERS.items():
            for service, sconfig in pconfig["services"].items():
                base = sconfig["base_cost"]
                category = sconfig["category"]
                region = random.choice(REGIONS[provider])

                for team in TEAMS:
                    for env in ENVS:
                        team_w = TEAM_WEIGHTS[team]
                        env_w = ENV_WEIGHTS[env]

                        noise = np.random.lognormal(0, 0.08)
                        anomaly_m, anomaly_id = get_anomaly_multiplier(
                            provider, service, team, env, day_idx
                        )

                        cost = (base * team_w * env_w * weekly_m *
                                monthly_m * growth_m * noise * anomaly_m)

                        # Daily → add some hours-level jitter (represent as daily summary)
                        cost = max(0.0, round(cost, 4))

                        records.append({
                            "date": date.date().isoformat(),
                            "provider": provider,
                            "service": service,
                            "category": category,
                            "team": team,
                            "environment": env,
                            "region": region,
                            "cost_usd": cost,
                            "anomaly_id": anomaly_id,
                            "is_anomaly": 1 if anomaly_id else 0,
                        })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df


def save_data(df: pd.DataFrame, output_dir: str = "data/raw") -> str:
    """Persist generated data as Parquet."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "billing_data.parquet")
    df.to_parquet(path, index=False)

    # Also save anomaly manifest
    manifest_path = os.path.join(output_dir, "anomaly_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(ANOMALY_EVENTS, f, indent=2)

    print(f"✅ Generated {len(df):,} billing records → {path}")
    print(f"✅ Anomaly manifest → {manifest_path}")
    return path


def load_or_generate() -> pd.DataFrame:
    """Load cached data or regenerate."""
    cache_path = os.path.join(os.path.dirname(__file__), "raw", "billing_data.parquet")
    if os.path.exists(cache_path):
        return pd.read_parquet(cache_path)
    df = generate_billing_data(90)
    save_data(df, os.path.join(os.path.dirname(__file__), "raw"))
    return df


if __name__ == "__main__":
    df = generate_billing_data(180)
    save_data(df, "raw")
    print(df.head())
    print(f"\nTotal spend: ${df['cost_usd'].sum():,.2f}")
    print(f"Anomalous records: {df['is_anomaly'].sum():,}")
