"""Anomalies router — serves detected anomalies with root cause data."""

from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])

_anomalies = None

def set_anomalies(anomalies_df: pd.DataFrame):
    global _anomalies
    _anomalies = anomalies_df


def _clean_val(v):
    """Recursively clean NaN/inf from any value."""
    import math
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    if isinstance(v, dict):
        return {k: _clean_val(vv) for k, vv in v.items()}
    if isinstance(v, list):
        return [_clean_val(x) for x in v]
    if isinstance(v, bool):
        return v
    # Handle numpy types
    try:
        import numpy as np
        if isinstance(v, (np.floating,)):
            return None if (np.isnan(v) or np.isinf(v)) else float(v)
        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.bool_):
            return bool(v)
    except Exception:
        pass
    return v


def _serialize(df: pd.DataFrame) -> list:
    df = df.copy()
    df["date"] = df["date"].astype(str)
    # Handle causal_chain column
    df["causal_chain"] = df["causal_chain"].apply(
        lambda x: x if isinstance(x, dict) else {}
    )
    # Convert boolean columns
    for col in ["is_stat_anomaly", "is_ml_anomaly", "is_dl_anomaly", "true_anomaly"]:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)
    # Clean anomaly_id
    if "anomaly_id" in df.columns:
        df["anomaly_id"] = df["anomaly_id"].apply(
            lambda x: str(x) if x is not None and str(x) not in ("nan", "None", "") else None
        )
    # Replace NaN in numeric columns
    for col in df.select_dtypes(include=["float64", "float32"]).columns:
        df[col] = df[col].fillna(0.0)
    # Replace inf
    df.replace([float("inf"), float("-inf")], 0.0, inplace=True)

    records = df.to_dict(orient="records")
    return [_clean_val(r) for r in records]


@router.get("/")
def list_anomalies(
    provider: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100),
):
    if _anomalies is None: return []
    df = _anomalies.copy()
    if provider:
        df = df[df["provider"] == provider]
    if team:
        df = df[df["team"] == team]
    if severity:
        df = df[df["severity_label"] == severity.upper()]
    df = df.sort_values(["date", "severity_score"], ascending=[False, False]).head(limit)
    return _serialize(df)


@router.get("/metrics")
def detection_metrics():
    if _anomalies is None: return {}
    from detection.ensemble import compute_metrics
    return compute_metrics(_anomalies)


@router.get("/recent")
def recent_anomalies(limit: int = 10):
    if _anomalies is None: return []
    df = _anomalies.sort_values(["date", "severity_score"], ascending=[False, False]).head(limit)
    return _serialize(df)


@router.get("/by-type")
def anomalies_by_type():
    if _anomalies is None or "type_label" not in _anomalies.columns:
        return []
    counts = _anomalies.groupby("type_label").agg(
        count=("severity_score", "count"),
        avg_severity=("severity_score", "mean"),
        total_cost=("cost_usd", "sum"),
    ).reset_index()
    return counts.to_dict(orient="records")
