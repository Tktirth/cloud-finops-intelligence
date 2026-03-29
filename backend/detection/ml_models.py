"""
ML-Based Anomaly Detection
Implements:
  1. Isolation Forest
  2. One-Class SVM
Both use engineered time-series cost features.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")


def engineer_features(group: pd.DataFrame) -> pd.DataFrame:
    """Engineer time-series features from a cost time series."""
    df = group.sort_values("date").copy()
    cost = df["cost_usd"]

    df["lag_1"] = cost.shift(1)
    df["lag_7"] = cost.shift(7)
    df["lag_14"] = cost.shift(14)
    df["rolling_mean_7"] = cost.rolling(7, min_periods=1).mean()
    df["rolling_std_7"] = cost.rolling(7, min_periods=1).std().fillna(0)
    df["rolling_mean_30"] = cost.rolling(30, min_periods=1).mean()
    df["rolling_std_30"] = cost.rolling(30, min_periods=1).std().fillna(0)
    df["pct_change_1"] = cost.pct_change(1).fillna(0)
    df["pct_change_7"] = cost.pct_change(7).fillna(0)
    df["ratio_to_rolling_mean"] = cost / (df["rolling_mean_7"] + 1e-6)
    df["day_of_week"] = pd.to_datetime(df["date"]).dt.dayofweek
    df["day_of_month"] = pd.to_datetime(df["date"]).dt.day

    return df.fillna(0)


FEATURE_COLS = [
    "cost_usd", "lag_1", "lag_7", "lag_14",
    "rolling_mean_7", "rolling_std_7", "rolling_mean_30", "rolling_std_30",
    "pct_change_1", "pct_change_7", "ratio_to_rolling_mean",
    "day_of_week", "day_of_month"
]


def run_ml_detection(daily_df: pd.DataFrame, contamination: float = 0.05) -> pd.DataFrame:
    """
    Run Isolation Forest + One-Class SVM per resource_key.
    Returns DataFrame with ml_anomaly flags and ml_score.
    """
    results = []

    for key, group in daily_df.groupby("resource_key"):
        group = group.sort_values("date").copy()

        if len(group) < 20:
            for _, row in group.iterrows():
                results.append({**row.to_dict(), "is_ml_anomaly": False, "ml_score": 0.0})
            continue

        feat_df = engineer_features(group)
        X = feat_df[FEATURE_COLS].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Isolation Forest
        iso = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
        iso_labels = iso.fit_predict(X_scaled)
        iso_scores = -iso.score_samples(X_scaled)  # higher = more anomalous

        # One-Class SVM
        try:
            oc_svm = OneClassSVM(nu=contamination, kernel="rbf", gamma="auto")
            svm_labels = oc_svm.fit_predict(X_scaled)
            svm_scores = -oc_svm.decision_function(X_scaled)
        except Exception:
            svm_labels = iso_labels.copy()
            svm_scores = iso_scores.copy()

        # Combine: both must agree for higher confidence, either for general flag
        combined_flag = (iso_labels == -1) | (svm_labels == -1)
        combined_score = (iso_scores + svm_scores) / 2

        for i, (_, row) in enumerate(group.iterrows()):
            results.append({
                **row.to_dict(),
                "is_ml_anomaly": bool(combined_flag[i]),
                "ml_score": float(combined_score[i]),
            })

    return pd.DataFrame(results)
