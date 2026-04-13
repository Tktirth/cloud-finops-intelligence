"""
Prophet Forecasting Model
Produces 7/30/90-day probabilistic forecasts per cost segment.

⚠️  WARNING: This module is BYPASSED in the production pipeline.
    main.py calls lgbm_model.py directly instead of the ensemble.
    Prophet requires pystan/cmdstan compilation which exceeds the
    512MB RAM limit on Render's free tier.
    It requires: prophet==1.1.5 (not in requirements.txt).
"""

import pandas as pd
import numpy as np
from prophet import Prophet
import warnings
warnings.filterwarnings("ignore")


def forecast_prophet(series: pd.DataFrame, horizon_days: int = 90) -> pd.DataFrame:
    """
    Fit Prophet on a daily cost series and return forecast with P10/P50/P90.
    series must have columns: ds (datetime), y (cost_usd)
    """
    if len(series) < 14:
        return pd.DataFrame()

    m = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.8,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0,
        uncertainty_samples=100,
    )

    try:
        m.fit(series[["ds", "y"]], iter=300)
        future = m.make_future_dataframe(periods=horizon_days, freq="D", include_history=False)
        forecast = m.predict(future)

        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        result.columns = ["date", "p50", "p10", "p90"]
        result["model"] = "prophet"

        # Clip negatives
        for col in ["p10", "p50", "p90"]:
            result[col] = result[col].clip(lower=0)

        return result
    except Exception as e:
        return pd.DataFrame()


def run_prophet_forecasts(daily_df: pd.DataFrame, horizons: list = [7, 30, 90]) -> dict:
    """
    Run Prophet forecasts for total spend, by provider, by team.
    Returns dict of DataFrames keyed by segment.
    """
    forecasts = {}

    # Total aggregate
    total = daily_df.groupby("date")["cost_usd"].sum().reset_index()
    total.columns = ["ds", "y"]
    total["ds"] = pd.to_datetime(total["ds"])

    for h in horizons:
        key = f"total_{h}d"
        forecasts[key] = forecast_prophet(total, horizon_days=h)

    # By provider
    for provider in daily_df["provider"].unique():
        sub = daily_df[daily_df["provider"] == provider].groupby("date")["cost_usd"].sum().reset_index()
        sub.columns = ["ds", "y"]
        sub["ds"] = pd.to_datetime(sub["ds"])
        for h in horizons:
            key = f"{provider}_{h}d"
            forecasts[key] = forecast_prophet(sub, horizon_days=h)

    # By team
    for team in daily_df["team"].unique():
        sub = daily_df[daily_df["team"] == team].groupby("date")["cost_usd"].sum().reset_index()
        sub.columns = ["ds", "y"]
        sub["ds"] = pd.to_datetime(sub["ds"])
        for h in horizons:
            key = f"team_{team}_{h}d"
            forecasts[key] = forecast_prophet(sub, horizon_days=h)

    return forecasts
