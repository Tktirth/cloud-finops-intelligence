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

import asyncio

_ml_error = None

async def run_ml_pipeline():
    global _ml_error
    try:
        print("\n" + "="*60)
        print("🚀 Cloud FinOps Intelligence — Starting ML Pipeline")
        print("="*60)

        # 1. Load data
        from data.db import get_store
        store = await asyncio.to_thread(get_store)

        from routers.overview import set_store
        set_store(store)

        # 2. Statistical detection
        from detection.statistical import run_statistical_detection
        stat_df = await asyncio.to_thread(run_statistical_detection, store.daily)

        # 3. ML detection
        from detection.ml_models import run_ml_detection
        ml_df = await asyncio.to_thread(run_ml_detection, store.daily, 0.03)

        # 4. Deep learning detection
        from detection.deep_learning import run_dl_detection
        dl_input = store.full.groupby(["date", "provider", "service", "category", "team", "environment"]).agg(
            cost_usd=("cost_usd", "sum"),
            is_anomaly=("is_anomaly", "max"),
            anomaly_id=("anomaly_id", lambda x: x.dropna().iloc[0] if x.dropna().any() else None),
        ).reset_index()
        dl_input["resource_key"] = dl_input["provider"] + "/" + dl_input["service"] + "/" + dl_input["team"] + "/" + dl_input["environment"]
        dl_df_agg = await asyncio.to_thread(run_dl_detection, dl_input, 3)
        dl_flags = dl_df_agg[["date", "resource_key", "is_dl_anomaly", "dl_score"]].copy()
        dl_df = store.daily.merge(dl_flags, on=["date", "resource_key"], how="left")
        dl_df["is_dl_anomaly"] = dl_df["is_dl_anomaly"].fillna(False).astype(bool)
        dl_df["dl_score"] = dl_df["dl_score"].fillna(0.0)

        # 5. Ensemble
        from detection.ensemble import run_ensemble
        from attribution.root_cause import run_attribution
        anomalies_df = await asyncio.to_thread(run_ensemble, stat_df, ml_df, dl_df)
        anomalies_df = await asyncio.to_thread(run_attribution, store.daily, anomalies_df)

        from routers.anomalies import set_anomalies
        set_anomalies(anomalies_df)

        # 6. Forecasting
        from forecasting.ensemble import run_ensemble_forecasts
        forecast_daily_df = store.full.groupby(["date", "provider", "team", "environment"])["cost_usd"].sum().reset_index()
        forecasts = await asyncio.to_thread(run_ensemble_forecasts, forecast_daily_df)

        from routers.forecasts import set_forecasts
        set_forecasts(forecasts)

        # 7. Budget breach prediction & alerts
        from alerts.engine import generate_alerts, predict_budget_breach
        alert_list = await asyncio.to_thread(generate_alerts, anomalies_df)
        breach_data = await asyncio.to_thread(predict_budget_breach, store.daily, forecasts)

        from routers.budgets_alerts import set_alert_data, set_budget_data
        set_alert_data(alert_list)
        set_budget_data(breach_data)

        print(f"\n✅ Pipeline complete!")
    except Exception as e:
        import traceback
        _ml_error = traceback.format_exc()
        print("\n❌ PIPELINE CRASHED:", e)
        print(_ml_error)

@app.on_event("startup")
async def startup_event():
    import asyncio
    asyncio.create_task(run_ml_pipeline())

@app.get("/api/debug-ml")
def debug_ml():
    return {"error": _ml_error}


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
