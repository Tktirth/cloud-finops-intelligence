"""
Forecasting Ensemble
Selects best model per segment via backtesting MAPE,
then blends Prophet + LightGBM outputs.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_percentage_error
import warnings
warnings.filterwarnings("ignore")

from forecasting.prophet_model import run_prophet_forecasts, forecast_prophet
from forecasting.lgbm_model import run_lgbm_forecasts, forecast_lgbm


def _mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """MAPE, avoiding division by zero."""
    mask = actual > 1.0
    if mask.sum() == 0:
        return 999.0
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def _wmape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Weighted MAPE."""
    if actual.sum() == 0:
        return 999.0
    return float(np.sum(np.abs(actual - predicted)) / (np.sum(np.abs(actual)) + 1e-8) * 100)


def backtest_segment(series: pd.DataFrame, test_days: int = 30) -> dict:
    """
    Hold out last `test_days` for backtesting.
    Returns MAPE for prophet and lgbm on the held-out period.
    """
    if len(series) < test_days + 14:
        return {"prophet_mape": 50.0, "lgbm_mape": 50.0}

    train = series.iloc[:-test_days]
    test = series.iloc[-test_days:]
    actual = test["cost_usd"].values

    train_prophet = train.rename(columns={"date": "ds", "cost_usd": "y"})
    train_prophet["ds"] = pd.to_datetime(train_prophet["ds"])

    p_fc = forecast_prophet(train_prophet, horizon_days=test_days)
    lg_fc = forecast_lgbm(train, horizon_days=test_days)

    results = {}
    if not p_fc.empty and len(p_fc) >= test_days:
        results["prophet_mape"] = _mape(actual, p_fc["p50"].values[:test_days])
    else:
        results["prophet_mape"] = 50.0

    if not lg_fc.empty and len(lg_fc) >= test_days:
        results["lgbm_mape"] = _mape(actual, lg_fc["p50"].values[:test_days])
    else:
        results["lgbm_mape"] = 50.0

    return results


def blend_forecasts(prophet_fc: pd.DataFrame, lgbm_fc: pd.DataFrame,
                    prophet_weight: float = 0.5) -> pd.DataFrame:
    """Weighted blend of two forecast DataFrames."""
    lgbm_weight = 1 - prophet_weight
    if prophet_fc.empty:
        return lgbm_fc
    if lgbm_fc.empty:
        return prophet_fc

    n = min(len(prophet_fc), len(lgbm_fc))
    blended = prophet_fc.head(n).copy()
    for col in ["p10", "p50", "p90"]:
        blended[col] = (
            prophet_fc[col].values[:n] * prophet_weight +
            lgbm_fc[col].values[:n] * lgbm_weight
        )
    blended["model"] = "ensemble"
    return blended


def run_ensemble_forecasts(daily_df: pd.DataFrame, horizons: list = [7, 30, 90]) -> dict:
    """
    Run both models and select best per segment via backtesting.
    Returns blended ensemble forecasts + per-model metrics.
    """
    print("🔮 Running Prophet forecasts...")
    prophet_fcs = run_prophet_forecasts(daily_df, horizons)

    print("🔮 Running LightGBM forecasts...")
    lgbm_fcs = run_lgbm_forecasts(daily_df, horizons)

    # Determine weights per segment via backtesting on 30-day window
    ensemble = {}
    max_h = max(horizons)

    # Total
    total_series = daily_df.groupby("date")["cost_usd"].sum().reset_index()
    bt = backtest_segment(total_series, test_days=30)
    prophet_w = 0.5
    if bt["lgbm_mape"] < bt["prophet_mape"]:
        prophet_w = 0.35  # lean toward lgbm
    else:
        prophet_w = 0.65  # lean toward prophet

    for h in horizons:
        pf = prophet_fcs.get(f"total_{h}d", pd.DataFrame())
        lf = lgbm_fcs.get(f"total_{h}d", pd.DataFrame())
        ensemble[f"total_{h}d"] = {
            "forecast": blend_forecasts(pf, lf, prophet_w).to_dict(orient="records"),
            "metrics": {**bt, "prophet_weight": prophet_w, "horizon_days": h},
        }

    # By provider
    for provider in daily_df["provider"].unique():
        sub = daily_df[daily_df["provider"] == provider].groupby("date")["cost_usd"].sum().reset_index()
        bt = backtest_segment(sub, test_days=30)
        pw = 0.65 if bt["prophet_mape"] < bt["lgbm_mape"] else 0.35
        for h in horizons:
            pf = prophet_fcs.get(f"{provider}_{h}d", pd.DataFrame())
            lf = lgbm_fcs.get(f"{provider}_{h}d", pd.DataFrame())
            ensemble[f"{provider}_{h}d"] = {
                "forecast": blend_forecasts(pf, lf, pw).to_dict(orient="records"),
                "metrics": {**bt, "prophet_weight": pw, "horizon_days": h},
            }

    # By team
    for team in daily_df["team"].unique():
        sub = daily_df[daily_df["team"] == team].groupby("date")["cost_usd"].sum().reset_index()
        bt = backtest_segment(sub, test_days=30)
        pw = 0.65 if bt["prophet_mape"] < bt["lgbm_mape"] else 0.35
        for h in horizons:
            pf = prophet_fcs.get(f"team_{team}_{h}d", pd.DataFrame())
            lf = lgbm_fcs.get(f"team_{team}_{h}d", pd.DataFrame())
            ensemble[f"team_{team}_{h}d"] = {
                "forecast": blend_forecasts(pf, lf, pw).to_dict(orient="records"),
                "metrics": {**bt, "prophet_weight": pw, "horizon_days": h},
            }

    return ensemble
