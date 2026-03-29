"""
Gradient Boosting Forecasting Model (scikit-learn based, no native dependencies)
Uses GradientBoostingRegressor with quantile loss for P10/P50/P90 forecasts.
Replaces LightGBM to avoid libomp dependency on macOS.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
import warnings
warnings.filterwarnings("ignore")


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_of_year"] = df["date"].dt.dayofyear
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    return df


def add_lag_features(df: pd.DataFrame, cost_col: str = "cost_usd") -> pd.DataFrame:
    df = df.sort_values("date").copy()
    for lag in [1, 2, 3, 7, 14, 21, 28]:
        df[f"lag_{lag}"] = df[cost_col].shift(lag)
    for window in [7, 14, 30]:
        df[f"roll_mean_{window}"] = df[cost_col].rolling(window, min_periods=1).mean()
        df[f"roll_std_{window}"] = df[cost_col].rolling(window, min_periods=1).std().fillna(0)
        df[f"roll_max_{window}"] = df[cost_col].rolling(window, min_periods=1).max()
    df["pct_change_1"] = df[cost_col].pct_change(1).fillna(0).clip(-5, 5)
    df["pct_change_7"] = df[cost_col].pct_change(7).fillna(0).clip(-5, 5)
    return df.fillna(0)


FEATURE_COLS = [
    "day_of_week", "day_of_month", "month", "week_of_year", "day_of_year", "is_weekend",
    "lag_1", "lag_2", "lag_3", "lag_7", "lag_14", "lag_21", "lag_28",
    "roll_mean_7", "roll_std_7", "roll_max_7",
    "roll_mean_14", "roll_std_14", "roll_max_14",
    "roll_mean_30", "roll_std_30", "roll_max_30",
    "pct_change_1", "pct_change_7",
]


def train_gbm_quantile(df: pd.DataFrame, cost_col: str = "cost_usd", quantile: float = 0.5) -> GradientBoostingRegressor:
    feat_df = add_time_features(df)
    feat_df = add_lag_features(feat_df, cost_col)
    feat_df = feat_df.dropna()

    X = feat_df[FEATURE_COLS].values
    y = feat_df[cost_col].values

    model = GradientBoostingRegressor(
        loss="quantile",
        alpha=quantile,
        n_estimators=150,
        max_depth=4,
        learning_rate=0.08,
        min_samples_leaf=3,
        random_state=42,
    )
    model.fit(X, y)
    return model


def forecast_lgbm(series: pd.DataFrame, horizon_days: int = 90) -> pd.DataFrame:
    """
    Forecast using GBM quantile regression.
    series: DataFrame with columns 'date' and 'cost_usd'
    """
    if len(series) < 21:
        return pd.DataFrame()

    try:
        m10 = train_gbm_quantile(series, quantile=0.1)
        m50 = train_gbm_quantile(series, quantile=0.5)
        m90 = train_gbm_quantile(series, quantile=0.9)

        last_date = pd.to_datetime(series["date"].max())
        working = series.copy()

        future_rows = []
        for i in range(horizon_days):
            future_date = last_date + pd.Timedelta(days=i + 1)
            feat_row = pd.DataFrame({"date": [future_date], "cost_usd": [0]})
            temp = pd.concat([working, feat_row], ignore_index=True)
            temp = add_time_features(temp)
            temp = add_lag_features(temp, "cost_usd")
            row_feats = temp.iloc[-1][FEATURE_COLS].values.reshape(1, -1)

            p50 = float(m50.predict(row_feats)[0])
            feat_row["cost_usd"] = max(p50, 0)
            working = pd.concat([working, feat_row], ignore_index=True)

            future_rows.append({
                "date": future_date,
                "p10": max(float(m10.predict(row_feats)[0]), 0),
                "p50": max(p50, 0),
                "p90": max(float(m90.predict(row_feats)[0]), 0),
                "model": "gbm",
            })

        return pd.DataFrame(future_rows)
    except Exception as e:
        return pd.DataFrame()


def run_lgbm_forecasts(daily_df: pd.DataFrame, horizons: list = [7, 30, 90]) -> dict:
    """Run GBM forecasts for total, by provider, and by team segments."""
    forecasts = {}
    max_h = max(horizons)

    total = daily_df.groupby("date")["cost_usd"].sum().reset_index()
    full = forecast_lgbm(total, horizon_days=max_h)
    for h in horizons:
        forecasts[f"total_{h}d"] = full.head(h) if not full.empty else pd.DataFrame()

    for provider in daily_df["provider"].unique():
        sub = daily_df[daily_df["provider"] == provider].groupby("date")["cost_usd"].sum().reset_index()
        full = forecast_lgbm(sub, horizon_days=max_h)
        for h in horizons:
            forecasts[f"{provider}_{h}d"] = full.head(h) if not full.empty else pd.DataFrame()

    for team in daily_df["team"].unique():
        sub = daily_df[daily_df["team"] == team].groupby("date")["cost_usd"].sum().reset_index()
        full = forecast_lgbm(sub, horizon_days=max_h)
        for h in horizons:
            forecasts[f"team_{team}_{h}d"] = full.head(h) if not full.empty else pd.DataFrame()

    return forecasts
