"""
Cloud FinOps Intelligence — FastAPI Main Application
Orchestrates: data loading → anomaly detection → forecasting → attribution → alerts
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI(
    title="Cloud FinOps Intelligence API",
    description="AI-Powered Multi-Cloud Cost Anomaly Detection & Spend Forecasting",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Startup: Run entire ML pipeline
# ─────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*60)
    print("🚀 Cloud FinOps Intelligence — Starting ML Pipeline")
    print("="*60)

    # 1. Load data
    print("\n📊 Step 1/6: Loading billing data...")
    from data.db import get_store
    store = get_store()

    # Register store with overview router
    from routers.overview import set_store
    set_store(store)

    # 2. Statistical detection
    print("\n🔍 Step 2/6: Running statistical anomaly detection (STL + GESD)...")
    from detection.statistical import run_statistical_detection
    stat_df = run_statistical_detection(store.daily)
    print(f"   → {stat_df['is_stat_anomaly'].sum()} statistical anomalies detected")

    # 3. ML detection
    print("\n🤖 Step 3/6: Running ML anomaly detection (Isolation Forest + One-Class SVM)...")
    from detection.ml_models import run_ml_detection
    ml_df = run_ml_detection(store.daily, contamination=0.03)
    print(f"   → {ml_df['is_ml_anomaly'].sum()} ML anomalies detected")

    # 4. Deep learning detection — run on aggregate + provider level for speed
    print("\n🧠 Step 4/6: Running LSTM Autoencoder detection...")
    from detection.deep_learning import run_dl_detection
    # Aggregate to provider+team level for DL (manageable number of time series)
    dl_input = store.full.groupby(["date", "provider", "service", "category", "team", "environment"]).agg(
        cost_usd=("cost_usd", "sum"),
        is_anomaly=("is_anomaly", "max"),
        anomaly_id=("anomaly_id", lambda x: x.dropna().iloc[0] if x.dropna().any() else None),
    ).reset_index()
    dl_input["resource_key"] = dl_input["provider"] + "/" + dl_input["service"] + "/" + dl_input["team"] + "/" + dl_input["environment"]
    dl_df_agg = run_dl_detection(dl_input, epochs=10)
    # Map DL flags back to full daily_df by resource_key
    dl_flags = dl_df_agg[["date", "resource_key", "is_dl_anomaly", "dl_score"]].copy()
    dl_df = store.daily.merge(dl_flags, on=["date", "resource_key"], how="left")
    dl_df["is_dl_anomaly"] = dl_df["is_dl_anomaly"].fillna(False).astype(bool)
    dl_df["dl_score"] = dl_df["dl_score"].fillna(0.0)
    print(f"   → {dl_df['is_dl_anomaly'].sum()} DL anomalies detected")

    # 5. Ensemble
    print("\n⚡ Step 5/6: Building anomaly ensemble + root cause attribution...")
    from detection.ensemble import run_ensemble
    from attribution.root_cause import run_attribution
    anomalies_df = run_ensemble(stat_df, ml_df, dl_df)
    anomalies_df = run_attribution(store.daily, anomalies_df)
    print(f"   → {len(anomalies_df)} total anomalies with attribution")

    from routers.anomalies import set_anomalies
    set_anomalies(anomalies_df)

    # 6. Forecasting — use aggregated daily data (not per-resource_key) for speed
    print("\n🔮 Step 6/6: Running ensemble forecasting (Prophet + GBM)...")
    from forecasting.ensemble import run_ensemble_forecasts
    # Aggregate to provider+team level for forecasting (much smaller: 180 rows per segment)
    forecast_df = store.full.groupby(["date", "provider", "team"])["cost_usd"].sum().reset_index()
    # Also build total and single-provider aggregates
    forecast_daily_df = store.full.groupby(["date", "provider", "team", "environment"])["cost_usd"].sum().reset_index()
    forecasts = run_ensemble_forecasts(forecast_daily_df)
    print(f"   → {len(forecasts)} forecast segments computed")

    from routers.forecasts import set_forecasts
    set_forecasts(forecasts)

    # 7. Budget breach prediction & alerts
    print("\n🚨 Computing budget breach predictions and alerts...")
    from alerts.engine import generate_alerts, predict_budget_breach
    alert_list = generate_alerts(anomalies_df)
    breach_data = predict_budget_breach(store.daily, forecasts)

    from routers.budgets_alerts import set_alert_data, set_budget_data
    set_alert_data(alert_list)
    set_budget_data(breach_data)

    print(f"\n✅ Pipeline complete!")
    print(f"   Anomalies: {len(anomalies_df)} | Alerts: {len(alert_list)} | Forecasts: {len(forecasts)}")
    print("="*60 + "\n")


# ─────────────────────────────────────────────
# Register routers
# ─────────────────────────────────────────────

from routers.overview import router as overview_router
from routers.anomalies import router as anomalies_router
from routers.forecasts import router as forecasts_router
from routers.budgets_alerts import budgets_router, alerts_router

app.include_router(overview_router)
app.include_router(anomalies_router)
app.include_router(forecasts_router)
app.include_router(budgets_router)
app.include_router(alerts_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "Cloud FinOps Intelligence API"}


@app.get("/")
def root():
    return {
        "name": "Cloud FinOps Intelligence",
        "version": "1.0.0",
        "docs": "/docs",
    }
