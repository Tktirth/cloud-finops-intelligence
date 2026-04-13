"""
Anomaly Ensemble — Combines statistical, ML, and DL detectors.
Produces unified severity score (0–100) and anomaly metadata.
"""

import numpy as np
import pandas as pd
from datetime import datetime
import os, json


ANOMALY_EVENTS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "anomaly_manifest.json")

ANOMALY_TYPE_LABELS = {
    "sudden_spike": "Sudden Cost Spike",
    "gradual_drift": "Gradual Cost Drift",
    "data_transfer_blast": "Data Transfer Blast",
    "correlated_spike": "Correlated Multi-Service Spike",
    "seasonal_deviation": "Seasonal Cost Deviation",
}


def _load_manifest() -> list:
    try:
        with open(ANOMALY_EVENTS_PATH) as f:
            return json.load(f)
    except Exception:
        return []


def compute_severity(stat_score: float, ml_score: float, dl_score: float,
                     stat_flag: bool, ml_flag: bool, dl_flag: bool) -> float:
    """
    Weighted severity score 0-100.
    Components: method agreement (40%) + raw scores (60%).
    """
    # Agreement component
    votes = int(stat_flag) + int(ml_flag) + int(dl_flag)
    agreement = (votes / 3) * 40

    # Score component — normalize each to 0-1 approximately
    stat_norm = min(stat_score / 6.0, 1.0) * 20
    ml_norm = min(ml_score / 2.0, 1.0) * 20
    dl_norm = min(dl_score / 0.1, 1.0) * 20

    severity = agreement + stat_norm + ml_norm + dl_norm
    return round(min(severity, 100.0), 1)


def label_severity(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    else:
        return "LOW"


def run_ensemble(stat_df: pd.DataFrame, ml_df: pd.DataFrame, dl_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge all detector outputs and produce a unified anomaly DataFrame.
    Only returns records flagged by at least one detector.
    """
    # Join on date + resource_key
    base_cols = ["date", "resource_key", "provider", "service", "team", "environment",
                 "cost_usd", "true_anomaly", "anomaly_id"]

    merged = stat_df[base_cols + ["is_stat_anomaly", "stat_score"]].copy()
    merged = merged.merge(
        ml_df[["date", "resource_key", "is_ml_anomaly", "ml_score"]],
        on=["date", "resource_key"], how="left"
    )
    merged = merged.merge(
        dl_df[["date", "resource_key", "is_dl_anomaly", "dl_score"]],
        on=["date", "resource_key"], how="left"
    )

    merged = merged.fillna({"is_ml_anomaly": False, "ml_score": 0.0,
                            "is_dl_anomaly": False, "dl_score": 0.0})

    merged["detected"] = (
        merged["is_stat_anomaly"] | merged["is_ml_anomaly"] | merged["is_dl_anomaly"]
    )

    merged["severity_score"] = merged.apply(
        lambda r: compute_severity(
            r["stat_score"], r["ml_score"], r["dl_score"],
            r["is_stat_anomaly"], r["is_ml_anomaly"], r["is_dl_anomaly"]
        ), axis=1
    )

    merged["severity_label"] = merged["severity_score"].apply(label_severity)

    # Only keep detected anomalies
    anomalies = merged[merged["detected"]].copy()

    # Enrich with manifest metadata
    manifest = {ev["id"]: ev for ev in _load_manifest()}
    anomalies["anomaly_type"] = anomalies["anomaly_id"].apply(
        lambda x: manifest.get(x, {}).get("type", "unknown") if pd.notna(x) else "detected"
    )
    anomalies["anomaly_description"] = anomalies["anomaly_id"].apply(
        lambda x: manifest.get(x, {}).get("description", "Potential cost anomaly detected") if pd.notna(x) else "Potential cost anomaly detected"
    )
    anomalies["root_cause"] = anomalies["anomaly_id"].apply(
        lambda x: manifest.get(x, {}).get("root_cause", "Under investigation") if pd.notna(x) else "Under investigation"
    )
    anomalies["type_label"] = anomalies["anomaly_type"].apply(
        lambda x: ANOMALY_TYPE_LABELS.get(x, "Unknown Anomaly")
    )
    # Store the actual vote count (0-3) — not just a boolean flag.
    # The alerts engine uses int(detector_votes) for severity weighting.
    anomalies["detector_votes"] = (
        anomalies["is_stat_anomaly"].astype(int) +
        anomalies["is_ml_anomaly"].astype(int) +
        anomalies["is_dl_anomaly"].astype(int)
    )
    anomalies["anomaly_id"] = anomalies["anomaly_id"].apply(
        lambda x: str(x) if pd.notna(x) and x else None
    )
    anomalies["true_anomaly"] = anomalies["true_anomaly"].fillna(False).astype(bool)

    return anomalies.sort_values(["date", "severity_score"], ascending=[False, False]).reset_index(drop=True)


def compute_metrics(anomalies: pd.DataFrame) -> dict:
    """Compute F1, precision, recall on labeled data."""
    tp = ((anomalies["detected"]) & (anomalies["true_anomaly"])).sum()
    fp = ((anomalies["detected"]) & (~anomalies["true_anomaly"].astype(bool))).sum()
    fn = (~(anomalies["detected"]) & (anomalies["true_anomaly"].astype(bool))).sum()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "f1": round(f1, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "false_negatives": int(fn),
    }
