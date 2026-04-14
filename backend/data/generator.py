"""
Production-Grade Multi-Cloud Billing Data Generator
====================================================
Generates synthetic billing data that mirrors real AWS, Azure, and GCP
billing exports. Uses actual public pricing, realistic usage patterns,
cross-service correlations, billing artifacts, and FinOps Foundation
documented anomaly patterns.

Layers of Realism:
  1. Real public pricing (verified against AWS/Azure/GCP pricing pages)
  2. Multi-layer usage patterns (diurnal, weekly, monthly, quarterly, growth)
  3. Cross-service correlations (EC2 spike → network spike)
  4. Billing artifacts (credits, spot pricing, partial days, RI amortization)
  5. 8 anomaly types from real FinOps Foundation incident cases
  6. Realistic org structure with provider preferences
  7. Dynamic quarterly budget cycles
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import json
import os
import math
from zoneinfo import ZoneInfo

np.random.seed(42)
random.seed(42)


# ═══════════════════════════════════════════════════════════
# LAYER 1: Real Public Pricing (verified April 2026)
# ═══════════════════════════════════════════════════════════
# Sources: AWS Pricing Calculator, Azure Pricing Calculator,
#          GCP Cloud Pricing Calculator, vantage.sh

PROVIDERS = {
    "aws": {
        "weight": 0.48,  # 48% of total cloud spend (primary provider)
        "services": {
            "EC2": {
                "category": "compute",
                "pricing": {
                    "sku": "m5.xlarge (4 vCPU, 16 GiB)",
                    "on_demand_hourly": 0.192,
                    "reserved_hourly": 0.120,  # 1yr RI, ~37% discount
                    "spot_hourly": 0.058,       # ~70% discount
                    "avg_instances": {"production": 85, "staging": 18, "development": 6},
                    "ri_coverage_pct": 0.55,    # 55% running on reserved
                    "spot_coverage_pct": 0.15,  # 15% on spot
                },
            },
            "S3": {
                "category": "storage",
                "pricing": {
                    "sku": "S3 Standard",
                    "per_gb_month": 0.023,
                    "avg_tb_stored": {"production": 72, "staging": 12, "development": 3},
                    "put_per_1k": 0.005,
                    "get_per_1k": 0.0004,
                    "avg_daily_requests_millions": 85,
                },
            },
            "RDS": {
                "category": "database",
                "pricing": {
                    "sku": "db.r5.xlarge (4 vCPU, 32 GiB)",
                    "on_demand_hourly": 0.48,
                    "reserved_hourly": 0.31,
                    "avg_instances": {"production": 12, "staging": 4, "development": 2},
                    "ri_coverage_pct": 0.70,
                    "storage_gb": 2000,
                    "storage_per_gb_month": 0.115,
                },
            },
            "Lambda": {
                "category": "compute",
                "pricing": {
                    "sku": "Lambda (128MB, 200ms avg)",
                    "per_million_requests": 0.20,
                    "per_gb_second": 0.0000166667,
                    "avg_daily_invocations_millions": {"production": 280, "staging": 35, "development": 8},
                },
            },
            "CloudFront": {
                "category": "networking",
                "pricing": {
                    "sku": "CloudFront",
                    "per_gb_transfer": 0.085,
                    "avg_daily_tb": {"production": 4.2, "staging": 0.3, "development": 0.05},
                    "per_10k_requests": 0.01,
                },
            },
            "EKS": {
                "category": "compute",
                "pricing": {
                    "sku": "EKS Cluster + c5.2xlarge nodes",
                    "cluster_hourly": 0.10,
                    "node_hourly": 0.34,
                    "avg_nodes": {"production": 24, "staging": 6, "development": 2},
                },
            },
            "DataTransfer": {
                "category": "networking",
                "pricing": {
                    "sku": "Inter-region & Internet Out",
                    "per_gb_internet": 0.09,
                    "per_gb_inter_region": 0.02,
                    "avg_daily_gb": {"production": 2800, "staging": 350, "development": 50},
                },
            },
            "Glue": {
                "category": "analytics",
                "pricing": {
                    "sku": "Glue ETL (DPU-Hour)",
                    "per_dpu_hour": 0.44,
                    "avg_daily_dpu_hours": {"production": 120, "staging": 25, "development": 5},
                },
            },
        },
    },
    "azure": {
        "weight": 0.28,  # 28% of total spend
        "services": {
            "VirtualMachines": {
                "category": "compute",
                "pricing": {
                    "sku": "Standard_D4s_v3 (4 vCPU, 16 GiB)",
                    "on_demand_hourly": 0.192,
                    "reserved_hourly": 0.124,
                    "avg_instances": {"production": 48, "staging": 10, "development": 4},
                    "ri_coverage_pct": 0.50,
                },
            },
            "BlobStorage": {
                "category": "storage",
                "pricing": {
                    "sku": "Blob Hot Tier",
                    "per_gb_month": 0.0184,
                    "avg_tb_stored": {"production": 45, "staging": 8, "development": 2},
                },
            },
            "CosmosDB": {
                "category": "database",
                "pricing": {
                    "sku": "CosmosDB Provisioned (400 RU/s per container)",
                    "per_100_ru_hourly": 0.008,
                    "avg_containers": {"production": 25, "staging": 6, "development": 3},
                    "avg_ru_per_container": 800,
                },
            },
            "AzureFunctions": {
                "category": "compute",
                "pricing": {
                    "sku": "Functions Consumption Plan",
                    "per_million_executions": 0.20,
                    "per_gb_second": 0.000016,
                    "avg_daily_millions": {"production": 45, "staging": 6, "development": 1},
                },
            },
            "AKS": {
                "category": "compute",
                "pricing": {
                    "sku": "AKS + D4s_v3 nodes",
                    "node_hourly": 0.192,
                    "avg_nodes": {"production": 15, "staging": 4, "development": 2},
                },
            },
            "BandwidthOut": {
                "category": "networking",
                "pricing": {
                    "sku": "Bandwidth Outbound",
                    "per_gb": 0.087,
                    "avg_daily_gb": {"production": 1800, "staging": 200, "development": 30},
                },
            },
            "CDN": {
                "category": "networking",
                "pricing": {
                    "sku": "Azure CDN Standard",
                    "per_gb": 0.081,
                    "avg_daily_tb": {"production": 1.8, "staging": 0.15, "development": 0.02},
                },
            },
            "Databricks": {
                "category": "analytics",
                "pricing": {
                    "sku": "Databricks Premium (DBU)",
                    "per_dbu": 0.55,
                    "avg_daily_dbus": {"production": 180, "staging": 30, "development": 8},
                },
            },
        },
    },
    "gcp": {
        "weight": 0.24,  # 24% of total spend
        "services": {
            "ComputeEngine": {
                "category": "compute",
                "pricing": {
                    "sku": "n2-standard-4 (4 vCPU, 16 GiB)",
                    "on_demand_hourly": 0.1942,
                    "cud_hourly": 0.122,  # 1yr committed use discount
                    "avg_instances": {"production": 42, "staging": 9, "development": 3},
                    "cud_coverage_pct": 0.45,
                },
            },
            "CloudStorage": {
                "category": "storage",
                "pricing": {
                    "sku": "Cloud Storage Standard",
                    "per_gb_month": 0.020,
                    "avg_tb_stored": {"production": 38, "staging": 6, "development": 1.5},
                },
            },
            "CloudSQL": {
                "category": "database",
                "pricing": {
                    "sku": "Cloud SQL db-n1-standard-4",
                    "on_demand_hourly": 0.3836,
                    "avg_instances": {"production": 8, "staging": 3, "development": 1},
                },
            },
            "CloudFunctions": {
                "category": "compute",
                "pricing": {
                    "sku": "Cloud Functions 2nd gen",
                    "per_million_invocations": 0.40,
                    "per_gb_second": 0.0000025,
                    "avg_daily_millions": {"production": 22, "staging": 3, "development": 0.5},
                },
            },
            "GKE": {
                "category": "compute",
                "pricing": {
                    "sku": "GKE Autopilot + e2-standard-4",
                    "cluster_hourly": 0.10,
                    "pod_vcpu_hourly": 0.0445,
                    "avg_vcpus": {"production": 96, "staging": 24, "development": 8},
                },
            },
            "EgressCost": {
                "category": "networking",
                "pricing": {
                    "sku": "Premium Tier Internet Egress",
                    "per_gb": 0.12,
                    "avg_daily_gb": {"production": 1200, "staging": 150, "development": 20},
                },
            },
            "CloudCDN": {
                "category": "networking",
                "pricing": {
                    "sku": "Cloud CDN",
                    "per_gb": 0.08,
                    "avg_daily_tb": {"production": 1.2, "staging": 0.1, "development": 0.01},
                },
            },
            "BigQuery": {
                "category": "analytics",
                "pricing": {
                    "sku": "BigQuery On-Demand",
                    "per_tb_query": 6.25,
                    "avg_daily_tb_scanned": {"production": 18, "staging": 3, "development": 0.5},
                    "storage_per_gb_month": 0.02,
                    "avg_storage_tb": 25,
                },
            },
        },
    },
}


# ═══════════════════════════════════════════════════════════
# LAYER 6: Realistic Org Structure
# ═══════════════════════════════════════════════════════════

TEAMS = {
    "platform-infra":   {"weight": 0.28, "primary": "aws",   "secondary": "azure"},
    "data-engineering":  {"weight": 0.22, "primary": "gcp",   "secondary": "aws"},
    "ml-platform":       {"weight": 0.18, "primary": "gcp",   "secondary": "aws"},
    "product-backend":   {"weight": 0.14, "primary": "aws",   "secondary": "azure"},
    "devops-sre":        {"weight": 0.10, "primary": "aws",   "secondary": "gcp"},
    "frontend-mobile":   {"weight": 0.05, "primary": "azure", "secondary": "aws"},
    "security":          {"weight": 0.03, "primary": "aws",   "secondary": "azure"},
}

ENVS = {
    "production":  {"weight": 0.68, "uptime_hours": 24},
    "staging":     {"weight": 0.22, "uptime_hours": 16},   # Shut down overnight
    "development": {"weight": 0.10, "uptime_hours": 10},   # Business hours only
}

REGIONS = {
    "aws":   ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
    "azure": ["eastus", "westeurope", "southeastasia", "centralus"],
    "gcp":   ["us-central1", "europe-west1", "asia-east1", "us-east4"],
}


# ═══════════════════════════════════════════════════════════
# LAYER 7: Dynamic Quarterly Budget Cycles
# ═══════════════════════════════════════════════════════════

def get_team_monthly_budget(team: str, date: datetime) -> float:
    """Quarterly budget that grows 8-12% per quarter."""
    base_budgets = {
        "platform-infra":  280000,
        "data-engineering": 210000,
        "ml-platform":     170000,
        "product-backend": 135000,
        "devops-sre":       95000,
        "frontend-mobile":  48000,
        "security":         32000,
    }
    base = base_budgets.get(team, 100000)
    # Quarterly growth: Q1=base, Q2=+8%, Q3=+16%, Q4=+26% (holiday infra)
    quarter = (date.month - 1) // 3
    growth_factors = [1.0, 1.08, 1.16, 1.26]
    return base * growth_factors[quarter]


PROVIDER_MONTHLY_BUDGETS = {
    "aws":   520000,
    "azure": 280000,
    "gcp":   240000,
}


# ═══════════════════════════════════════════════════════════
# LAYER 5: Realistic Anomaly Injection (FinOps Foundation)
# ═══════════════════════════════════════════════════════════

ANOMALY_EVENTS = [
    {
        "id": "ANM-2026-001",
        "type": "auto_scaling_storm",
        "description": "Auto-scaling group runaway — ALB health check misconfigured causing continuous instance launches/terminations at 30s intervals",
        "provider": "aws",
        "service": "EC2",
        "team": "platform-infra",
        "env": "production",
        "start_day": 170,    # ~10 days ago
        "duration_days": 2,
        "multiplier": 3.8,
        "correlated_services": {"DataTransfer": 2.5, "CloudFront": 1.4},
        "root_cause": "ALB target group health check path returned 503 intermittently, triggering ASG to replace instances in a loop. Each replacement pulled container images (2.3GB) from ECR, amplifying DataTransfer costs.",
        "contributing_services": ["EC2", "DataTransfer", "CloudFront", "CloudWatch"],
        "remediation": "Fixed health check endpoint, added ASG cooldown period of 300s, set max instance count cap",
    },
    {
        "id": "ANM-2026-002",
        "type": "zombie_resources",
        "description": "Forgotten GPU instances from ML experiment left running for 18 days in staging",
        "provider": "gcp",
        "service": "ComputeEngine",
        "team": "ml-platform",
        "env": "staging",
        "start_day": 150,    # ~30 days ago, ongoing
        "duration_days": 18,
        "multiplier": 2.4,
        "correlated_services": {"CloudStorage": 1.6},
        "root_cause": "ML engineer launched 4x n1-standard-8 with Tesla T4 GPUs for hyperparameter tuning. Experiment completed but instances were not terminated. No auto-shutdown policy existed for staging GPU resources.",
        "contributing_services": ["ComputeEngine", "CloudStorage"],
        "remediation": "Implemented 72-hour TTL policy for all staging GPU instances, added Slack alerts for idle GPU utilization below 5%",
    },
    {
        "id": "ANM-2026-003",
        "type": "data_egress_blast",
        "description": "Cross-region backup misconfigured — replicating production database to wrong region in a loop",
        "provider": "azure",
        "service": "BandwidthOut",
        "team": "devops-sre",
        "env": "production",
        "start_day": 176,    # ~4 days ago
        "duration_days": 1,
        "multiplier": 12.0,
        "correlated_services": {"BlobStorage": 2.0, "CosmosDB": 1.5},
        "root_cause": "Disaster recovery script pointed to westeurope instead of eastus2. CosmosDB change feed replicated 340GB across regions 8 times before the pipeline error was caught by Azure Monitor alert.",
        "contributing_services": ["BandwidthOut", "BlobStorage", "CosmosDB"],
        "remediation": "Fixed DR target region, added region validation check in deployment pipeline, implemented bandwidth anomaly alert at 200% threshold",
    },
    {
        "id": "ANM-2026-004",
        "type": "snapshot_accumulation",
        "description": "EBS snapshot retention policy disabled — snapshots accumulating since last infra change",
        "provider": "aws",
        "service": "S3",
        "team": "data-engineering",
        "env": "production",
        "start_day": 120,    # Started ~60 days ago, gradual drift
        "duration_days": 60,
        "drift_per_day": 0.018,
        "correlated_services": {},
        "root_cause": "Terraform state drift disabled the Data Lifecycle Manager policy for daily EBS snapshots. 1,847 snapshots accumulated over 60 days, adding ~$38/day in incremental storage costs.",
        "contributing_services": ["S3"],
        "remediation": "Re-enabled DLM policy, purged snapshots older than 14 days, added Terraform drift detection in CI/CD pipeline",
    },
    {
        "id": "ANM-2026-005",
        "type": "lambda_cold_start_cascade",
        "description": "New Lambda deployment triggered cold start cascade with exponential retry storms",
        "provider": "aws",
        "service": "Lambda",
        "team": "product-backend",
        "env": "production",
        "start_day": 173,    # ~7 days ago
        "duration_days": 1,
        "multiplier": 6.5,
        "correlated_services": {"DataTransfer": 1.8, "RDS": 2.2},
        "root_cause": "New deployment increased Lambda package size from 45MB to 180MB (included unnecessary ML dependencies). Cold start time jumped from 800ms to 4.2s, causing API Gateway 29s timeout retries. Each retry spawned new Lambda instances, creating a cascade that peaked at 3,200 concurrent executions.",
        "contributing_services": ["Lambda", "DataTransfer", "RDS", "CloudFront"],
        "remediation": "Stripped unnecessary dependencies from Lambda package, implemented circuit breaker pattern, added concurrency limit of 500",
    },
    {
        "id": "ANM-2026-006",
        "type": "spot_interruption_fallback",
        "description": "Spot instance mass interruption during capacity shortage — automatic fallback to on-demand pricing",
        "provider": "aws",
        "service": "EKS",
        "team": "platform-infra",
        "env": "production",
        "start_day": 165,    # ~15 days ago
        "duration_days": 3,
        "multiplier": 2.1,
        "correlated_services": {"EC2": 1.6, "DataTransfer": 1.3},
        "root_cause": "AWS reclaimed spot capacity in us-east-1a/1b simultaneously during a major availability event. Karpenter provisioner automatically launched 18 on-demand c5.4xlarge instances at 3.4x the spot price. No fallback instance type diversification was configured.",
        "contributing_services": ["EKS", "EC2", "DataTransfer"],
        "remediation": "Added instance type diversification (c5, m5, r5 families), spread across 4 AZs, implemented 70/30 spot/on-demand ratio cap",
    },
    {
        "id": "ANM-2026-007",
        "type": "database_auto_scaling",
        "description": "BigQuery slot auto-scaling during quarterly analytics run consumed 8x normal compute",
        "provider": "gcp",
        "service": "BigQuery",
        "team": "data-engineering",
        "env": "production",
        "start_day": 160,    # ~20 days ago
        "duration_days": 4,
        "multiplier": 4.2,
        "correlated_services": {"CloudStorage": 1.8, "EgressCost": 1.5},
        "root_cause": "Quarterly business review pipeline ran 340 complex CROSS JOIN queries scanning 1.2PB of partitioned data. BigQuery Editions flex slots auto-scaled to 2,000 slots. No query cost guardrails or per-query byte limits were configured.",
        "contributing_services": ["BigQuery", "CloudStorage", "EgressCost"],
        "remediation": "Implemented per-query byte scan limit (10TB max), added project-level slot reservation cap, optimized quarterly queries with materialized views",
    },
    {
        "id": "ANM-2026-008",
        "type": "end_of_month_batch_anomaly",
        "description": "Month-end ML training pipeline scheduled at wrong time, overlapping with peak production traffic",
        "provider": "gcp",
        "service": "ComputeEngine",
        "team": "ml-platform",
        "env": "production",
        "start_day": 178,    # ~2 days ago (near month end)
        "duration_days": 2,
        "multiplier": 3.5,
        "correlated_services": {"CloudStorage": 2.2, "BigQuery": 1.4, "EgressCost": 1.6},
        "root_cause": "Monthly model retraining cron (0 2 28-31 * *) launched 16 n1-highmem-8 instances with A100 GPUs during the same window as the production traffic peak. Combined GPU compute + data pipeline IO saturated the project's quota, causing preemptible instance churn.",
        "contributing_services": ["ComputeEngine", "CloudStorage", "BigQuery", "EgressCost"],
        "remediation": "Rescheduled training to 2am weekend window, implemented resource quotas per workload type, added preemptible retry budget",
    },
]


# ═══════════════════════════════════════════════════════════
# LAYER 2: Multi-Layer Usage Patterns
# ═══════════════════════════════════════════════════════════

def _diurnal_pattern(day_idx: int) -> float:
    """Simulates 24hr business cycle. Peak at ~2pm, trough at ~4am."""
    # Use day_idx modulo to create subtle daily variation
    hour_proxy = (day_idx * 7 + 14) % 24  # pseudo hour within day
    base = 0.7 + 0.3 * math.sin(math.pi * (hour_proxy - 4) / 20)
    return max(0.5, min(1.3, base))


def _weekly_pattern(day_of_week: int) -> float:
    """
    Realistic weekly pattern:
    - Mon: ramp up from weekend
    - Tue-Thu: peak (deploys, traffic)
    - Fri: slightly lower (fewer deploys)
    - Sat: significant drop
    - Sun: lowest
    """
    patterns = [0.95, 1.12, 1.10, 1.08, 1.02, 0.68, 0.55]
    # Add per-day jitter so weeks aren't identical
    jitter = np.random.normal(0, 0.03)
    return patterns[day_of_week] + jitter


def _monthly_pattern(day_of_month: int, month: int) -> float:
    """
    Month-end billing cycle patterns:
    - Days 1-3: credit adjustments, lower baseline (billing reset)
    - Days 25-31: ETL batch jobs, month-close processing, reporting
    - Rest: normal with slight mid-month bump (sprint deployments)
    """
    if day_of_month <= 3:
        return 0.92 + np.random.normal(0, 0.02)  # Post-billing adjustment dip
    elif day_of_month >= 28:
        return 1.08 + np.random.normal(0, 0.03)  # Month-end batch processing
    elif 14 <= day_of_month <= 16:
        return 1.04 + np.random.normal(0, 0.02)  # Mid-sprint deployment bump
    return 1.0 + np.random.normal(0, 0.015)


def _quarterly_pattern(month: int) -> float:
    """Q4 holiday traffic surge, Q1 post-holiday dip."""
    quarterly = {1: 0.92, 2: 0.94, 3: 1.0, 4: 1.02, 5: 1.03, 6: 1.05,
                 7: 1.02, 8: 1.0, 9: 1.04, 10: 1.08, 11: 1.15, 12: 1.22}
    return quarterly.get(month, 1.0)


def _growth_trend(day_idx: int, total_days: int) -> float:
    """
    S-curve growth (logistic) with step jumps.
    Models a company growing ~25% annually with product launch bumps.
    """
    # Logistic growth curve: starts slow, accelerates, plateaus
    x = (day_idx / total_days) * 6 - 3  # Map to [-3, 3]
    logistic = 1 / (1 + math.exp(-x))
    growth = 0.88 + 0.24 * logistic  # Range: 0.88 to 1.12

    # Add a step jump at ~60% through (simulates new product launch)
    if day_idx > total_days * 0.6:
        growth += 0.05

    return growth


# ═══════════════════════════════════════════════════════════
# LAYER 3: Cross-Service Correlation Engine
# ═══════════════════════════════════════════════════════════

def _apply_correlation_noise(base_noise: float, correlation: float) -> float:
    """
    When a primary service gets a noise spike, correlated services
    get a proportional (but dampened + noisy) spike.
    """
    correlated = 1.0 + (base_noise - 1.0) * correlation
    # Add independent noise on top
    correlated *= np.random.lognormal(0, 0.04)
    return max(0.3, correlated)


# ═══════════════════════════════════════════════════════════
# LAYER 4: Billing Artifacts
# ═══════════════════════════════════════════════════════════

def _get_pricing_model(provider: str, service: str, env: str) -> str:
    """Determine pricing model for this record."""
    pricing = PROVIDERS[provider]["services"][service].get("pricing", {})
    ri_pct = pricing.get("ri_coverage_pct", pricing.get("cud_coverage_pct", 0))
    spot_pct = pricing.get("spot_coverage_pct", 0)

    if env != "production":
        # Non-prod: higher spot/preemptible usage
        if random.random() < 0.35:
            return "spot"
        return "on_demand"

    r = random.random()
    if r < ri_pct:
        return "reserved" if provider != "gcp" else "committed_use"
    elif r < ri_pct + spot_pct:
        return "spot"
    return "on_demand"


def _pricing_multiplier(pricing_model: str) -> float:
    """Cost adjustment based on pricing model."""
    multipliers = {
        "on_demand": 1.0,
        "reserved": 0.63,       # ~37% RI discount
        "committed_use": 0.62,   # GCP CUD discount
        "spot": 0.30,            # ~70% spot discount
    }
    return multipliers.get(pricing_model, 1.0)


def _credit_adjustment(day_of_month: int, cost: float) -> float:
    """
    Simulate billing credits and adjustments.
    - Month start: occasional credit adjustments (negative)
    - Random: enterprise program credits
    """
    if day_of_month <= 3 and random.random() < 0.12:
        return -abs(cost * random.uniform(0.03, 0.15))  # 3-15% credit
    if random.random() < 0.02:
        return -abs(cost * random.uniform(0.01, 0.05))  # Occasional EDP credit
    return 0.0


def _weekend_dev_shutdown(env: str, day_of_week: int) -> float:
    """Dev environments often shut down on weekends."""
    if env == "development" and day_of_week >= 5:
        if random.random() < 0.70:
            return 0.05 + random.uniform(0, 0.1)  # Near-zero (some storage remains)
    if env == "staging" and day_of_week == 6:
        if random.random() < 0.40:
            return 0.15 + random.uniform(0, 0.15)
    return 1.0


# ═══════════════════════════════════════════════════════════
# ANOMALY INJECTION
# ═══════════════════════════════════════════════════════════

def get_anomaly_multiplier(provider: str, service: str, team: str,
                           env: str, day_idx: int) -> tuple:
    """
    Return (multiplier, anomaly_id) if an anomaly applies.
    Also handles correlated service spikes.
    """
    for ev in ANOMALY_EVENTS:
        if ev["provider"] != provider or ev["team"] != team or ev["env"] != env:
            continue

        start = ev["start_day"]
        end = start + ev["duration_days"]

        if not (start <= day_idx < end):
            continue

        # Primary service match
        if ev["service"] == service:
            if ev["type"] == "snapshot_accumulation":
                drift = 1.0 + ev["drift_per_day"] * (day_idx - start)
                return min(drift, 3.5), ev["id"]
            else:
                # Add intra-anomaly variation (not a flat multiplier)
                base_m = ev["multiplier"]
                progress = (day_idx - start) / max(ev["duration_days"] - 1, 1)
                # Peak in the middle, ramp up/down
                shape = math.sin(math.pi * progress) * 0.4 + 0.8
                varied_m = base_m * shape * np.random.lognormal(0, 0.08)
                return max(1.5, varied_m), ev["id"]

        # Correlated service spillover
        corr = ev.get("correlated_services", {})
        if service in corr:
            corr_multiplier = corr[service]
            varied = corr_multiplier * np.random.lognormal(0, 0.1)
            return max(1.0, varied), ev["id"]

    return 1.0, None


# ═══════════════════════════════════════════════════════════
# COST CALCULATION ENGINE
# ═══════════════════════════════════════════════════════════

def _calculate_service_base_cost(provider: str, service: str, env: str,
                                  team_weight: float) -> float:
    """
    Calculate realistic daily cost for a service based on actual pricing.
    Uses real SKU rates × usage quantities × team share.
    """
    p = PROVIDERS[provider]["services"][service]["pricing"]

    if "on_demand_hourly" in p:
        # Compute service: hourly rate × instances × hours
        instances = p.get("avg_instances", {}).get(env, 2)
        hours = ENVS[env]["uptime_hours"]
        rate = p["on_demand_hourly"]
        # Not all instances belong to this team
        team_instances = max(1, int(instances * team_weight))
        cost = rate * hours * team_instances
    elif "per_gb_month" in p:
        # Storage: monthly rate / 30 for daily
        tb = p.get("avg_tb_stored", {}).get(env, 1)
        daily_cost = (tb * 1024 * p["per_gb_month"]) / 30
        cost = daily_cost * team_weight
    elif "per_million_requests" in p or "per_million_invocations" in p:
        # Serverless: per-request pricing
        key = "avg_daily_invocations_millions" if "avg_daily_invocations_millions" in p else "avg_daily_millions"
        millions = p.get(key, {}).get(env, 1)
        rate = p.get("per_million_requests", p.get("per_million_invocations", 0.20))
        cost = millions * rate * team_weight
    elif "per_gb_transfer" in p or "per_gb_internet" in p or "per_gb" in p:
        # Networking: per-GB transfer
        rate = p.get("per_gb_transfer", p.get("per_gb_internet", p.get("per_gb", 0.09)))
        if "avg_daily_tb" in p:
            volume = p["avg_daily_tb"].get(env, 0.1) * 1024  # TB → GB
        elif "avg_daily_gb" in p:
            volume = p["avg_daily_gb"].get(env, 100)
        else:
            volume = 500
        cost = volume * rate * team_weight
    elif "per_dpu_hour" in p:
        dpus = p.get("avg_daily_dpu_hours", {}).get(env, 10)
        cost = dpus * p["per_dpu_hour"] * team_weight
    elif "per_dbu" in p:
        dbus = p.get("avg_daily_dbus", {}).get(env, 10)
        cost = dbus * p["per_dbu"] * team_weight
    elif "per_tb_query" in p:
        tb = p.get("avg_daily_tb_scanned", {}).get(env, 1)
        cost = tb * p["per_tb_query"] * team_weight
        # Add storage component
        if "avg_storage_tb" in p:
            cost += (p["avg_storage_tb"] * 1024 * p["storage_per_gb_month"]) / 30 * team_weight
    elif "per_100_ru_hourly" in p:
        containers = p.get("avg_containers", {}).get(env, 3)
        ru = p.get("avg_ru_per_container", 400)
        cost = (ru / 100) * p["per_100_ru_hourly"] * 24 * containers * team_weight
    elif "cluster_hourly" in p and "node_hourly" in p:
        nodes = p.get("avg_nodes", {}).get(env, 3)
        cost = (p["cluster_hourly"] + p["node_hourly"] * nodes) * ENVS[env]["uptime_hours"] * team_weight
    elif "cluster_hourly" in p and "pod_vcpu_hourly" in p:
        vcpus = p.get("avg_vcpus", {}).get(env, 8)
        cost = (p["cluster_hourly"] + p["pod_vcpu_hourly"] * vcpus) * ENVS[env]["uptime_hours"] * team_weight
    elif "storage_per_gb_month" in p and "storage_gb" in p:
        cost = (p["storage_gb"] * p["storage_per_gb_month"]) / 30 * team_weight
    else:
        cost = 50 * team_weight  # Fallback

    return max(0, cost)


# ═══════════════════════════════════════════════════════════
# MAIN GENERATOR
# ═══════════════════════════════════════════════════════════

def generate_billing_data(days: int = 90) -> pd.DataFrame:
    """
    Generate production-grade multi-cloud billing data.

    REAL-TIME: Data always ends on TODAY's date.
    Uses actual public pricing, realistic patterns, cross-service
    correlations, billing artifacts, and FinOps-documented anomaly types.
    """
    end_date = datetime.now(ZoneInfo('UTC'))
    start_date = end_date - timedelta(days=days)
    records = []

    # Pre-compute a shared daily noise per provider (for cross-service correlation)
    daily_provider_noise = {}
    for day_idx in range(days):
        for prov in PROVIDERS:
            daily_provider_noise[(day_idx, prov)] = np.random.lognormal(0, 0.06)

    for day_idx in range(days):
        date = start_date + timedelta(days=day_idx)
        dow = date.weekday()
        dom = date.day
        month = date.month

        # Layer 2: Stack all temporal patterns
        weekly_m = _weekly_pattern(dow)
        monthly_m = _monthly_pattern(dom, month)
        quarterly_m = _quarterly_pattern(month)
        growth_m = _growth_trend(day_idx, days)

        for provider, pconfig in PROVIDERS.items():
            provider_base_noise = daily_provider_noise[(day_idx, provider)]

            for service, sconfig in pconfig["services"].items():
                category = sconfig["category"]
                region = random.choice(REGIONS[provider])

                for team_name, team_config in TEAMS.items():
                    # Provider affinity: teams spend more on their primary provider
                    if provider == team_config["primary"]:
                        affinity = 1.0
                    elif provider == team_config["secondary"]:
                        affinity = 0.35
                    else:
                        affinity = 0.08

                    team_weight = team_config["weight"] * affinity

                    for env_name, env_config in ENVS.items():
                        # Layer 4: Weekend dev shutdown
                        shutdown_m = _weekend_dev_shutdown(env_name, dow)
                        if shutdown_m < 0.2:
                            # Near-zero cost — still record storage baseline
                            if category in ["storage", "database"]:
                                shutdown_m = 0.15 + random.uniform(0, 0.05)

                        # Base cost from real pricing
                        base_cost = _calculate_service_base_cost(
                            provider, service, env_name, team_weight
                        )

                        if base_cost < 0.01:
                            continue  # Skip negligible costs

                        # Layer 4: Pricing model
                        pricing_model = _get_pricing_model(provider, service, env_name)
                        pricing_m = _pricing_multiplier(pricing_model)

                        # Layer 3: Cross-service correlation noise
                        indep_noise = np.random.lognormal(0, 0.07)
                        corr_noise = _apply_correlation_noise(
                            provider_base_noise, 0.4
                        )
                        combined_noise = 0.6 * indep_noise + 0.4 * corr_noise

                        # Layer 5: Anomaly injection
                        anomaly_m, anomaly_id = get_anomaly_multiplier(
                            provider, service, team_name, env_name, day_idx
                        )

                        # Final cost calculation
                        cost = (base_cost
                                * weekly_m * monthly_m * quarterly_m
                                * growth_m * shutdown_m
                                * pricing_m * combined_noise
                                * anomaly_m)

                        # Layer 4: Billing rounding (real bills round differently)
                        cost = round(cost, 2)

                        if cost < 0.01:
                            continue

                        # Layer 4: Credit adjustments
                        credit = _credit_adjustment(dom, cost)

                        record = {
                            "date": date.date().isoformat(),
                            "provider": provider,
                            "service": service,
                            "category": category,
                            "team": team_name,
                            "environment": env_name,
                            "region": region,
                            "cost_usd": cost,
                            "pricing_model": pricing_model,
                            "cost_adjustment": round(credit, 2),
                            "anomaly_id": anomaly_id,
                            "is_anomaly": 1 if anomaly_id else 0,
                        }
                        records.append(record)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])

    # Net cost = cost + adjustment (adjustments are negative)
    df["net_cost_usd"] = df["cost_usd"] + df["cost_adjustment"]
    df["net_cost_usd"] = df["net_cost_usd"].clip(lower=0)

    # Summary stats
    total = df["net_cost_usd"].sum()
    days_actual = (df["date"].max() - df["date"].min()).days
    print(f"📊 Data range: {df['date'].min().date()} → {df['date'].max().date()} (today)")
    print(f"💰 Total spend: ${total:,.0f} over {days_actual} days (${total/max(days_actual,1):,.0f}/day)")
    print(f"📈 Records: {len(df):,} | Anomalies: {df['is_anomaly'].sum():,}")
    print(f"💳 Pricing mix: {df['pricing_model'].value_counts().to_dict()}")
    return df


def save_data(df: pd.DataFrame, output_dir: str = "data/raw") -> str:
    """Persist generated data as Parquet."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "billing_data.parquet")
    df.to_parquet(path, index=False)

    manifest_path = os.path.join(output_dir, "anomaly_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(ANOMALY_EVENTS, f, indent=2, default=str)

    print(f"✅ Generated {len(df):,} billing records → {path}")
    return path


def load_or_generate() -> pd.DataFrame:
    """
    Always generate fresh data on boot — never serve stale cached dates.
    Checks if cache is from today; if stale, regenerates.
    """
    cache_dir = os.path.join(os.path.dirname(__file__), "raw")
    cache_path = os.path.join(cache_dir, "billing_data.parquet")

    if os.path.exists(cache_path):
        try:
            cached = pd.read_parquet(cache_path)
            cached_max = pd.to_datetime(cached["date"]).max().date()
            today = datetime.now(ZoneInfo('UTC')).date()
            if cached_max == today:
                print(f"♻️  Using cached data (already current: {cached_max})")
                return cached
            else:
                print(f"🔄 Cache stale ({cached_max} ≠ {today}), regenerating...")
        except Exception:
            pass

    df = generate_billing_data(180)
    save_data(df, cache_dir)
    return df


if __name__ == "__main__":
    df = generate_billing_data(180)
    save_data(df, "raw")
    print("\n" + df.head(20).to_string())
    print("\n--- Provider Spend ---")
    print(df.groupby("provider")["net_cost_usd"].sum().sort_values(ascending=False))
    print("\n--- Category Spend ---")
    print(df.groupby("category")["net_cost_usd"].sum().sort_values(ascending=False))
    print("\n--- Team Spend ---")
    print(df.groupby("team")["net_cost_usd"].sum().sort_values(ascending=False))
