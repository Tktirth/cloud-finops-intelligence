"""
Statistical Anomaly Detection
Implements:
  1. Z-score with seasonal decomposition (STL)
  2. Generalized Extreme Studentized Deviate (GESD)
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL
from scipy import stats


def zscore_stl_detection(series: pd.Series, period: int = 7, threshold: float = 3.0) -> pd.Series:
    """
    Apply STL decomposition, then detect anomalies as residuals > threshold*std.
    Returns boolean Series aligned with input index.
    """
    if len(series) < 2 * period:
        return pd.Series([False] * len(series), index=series.index)

    try:
        stl = STL(series, period=period, robust=True)
        result = stl.fit()
        residuals = result.resid
        z_scores = np.abs(stats.zscore(residuals))
        return pd.Series(z_scores > threshold, index=series.index)
    except Exception:
        # Fallback: plain Z-score
        z = np.abs(stats.zscore(series))
        return pd.Series(z > threshold, index=series.index)


def gesd_test(data: np.ndarray, alpha: float = 0.05, max_outliers: int = None) -> list:
    """
    Generalized Extreme Studentized Deviate test.
    Returns list of outlier indices.
    """
    if max_outliers is None:
        max_outliers = max(1, len(data) // 10)

    suspected = []
    working = data.copy().astype(float)
    original_indices = list(range(len(data)))
    remaining_indices = list(range(len(data)))

    for i in range(1, max_outliers + 1):
        n = len(working)
        if n < 3:
            break
        mean = np.mean(working)
        std = np.std(working, ddof=1)
        if std == 0:
            break
        scores = np.abs(working - mean) / std
        max_idx = np.argmax(scores)
        R = scores[max_idx]

        # Critical value via t-distribution
        p = 1 - alpha / (2 * (n - i + 1))
        t_crit = stats.t.ppf(p, df=n - i - 1) if n - i - 1 > 0 else 0
        lam = ((n - i) * t_crit) / np.sqrt((n - i - 1 + t_crit**2) * (n - i + 1))

        if R > lam:
            suspected.append(remaining_indices[max_idx])
            working = np.delete(working, max_idx)
            remaining_indices.pop(max_idx)
        else:
            break

    return suspected


def run_statistical_detection(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run statistical anomaly detection on all resource_key time series.
    Returns DataFrame with columns: date, resource_key, is_stat_anomaly, stat_score
    """
    results = []

    for key, group in daily_df.groupby("resource_key"):
        group = group.sort_values("date").copy()
        series = group.set_index("date")["cost_usd"]

        # STL + Z-score
        stl_flags = zscore_stl_detection(series, period=7, threshold=3.0)

        # GESD on the same series
        gesd_flags_idx = set(gesd_test(series.values, alpha=0.05))
        gesd_flags = pd.Series(
            [i in gesd_flags_idx for i in range(len(series))],
            index=series.index
        )

        # Combine: flag if either method detects
        combined = stl_flags | gesd_flags

        # Compute Z-score for severity
        z_raw = np.abs(stats.zscore(series.values)) if len(series) > 2 else np.zeros(len(series))

        for i, (date, row) in enumerate(group.iterrows()):
            results.append({
                "date": row["date"],
                "resource_key": key,
                "provider": key.split("/")[0],
                "service": key.split("/")[1],
                "team": key.split("/")[2],
                "environment": key.split("/")[3],
                "cost_usd": row["cost_usd"],
                "is_stat_anomaly": bool(combined.iloc[i]) if i < len(combined) else False,
                "stat_score": float(z_raw[i]) if i < len(z_raw) else 0.0,
                "true_anomaly": bool(row.get("is_anomaly", 0)),
                "anomaly_id": row.get("anomaly_id"),
            })

    return pd.DataFrame(results)
