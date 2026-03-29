"""Forecasts router — serves ensemble forecast data."""

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])

_forecasts = {}

def set_forecasts(forecasts: dict):
    global _forecasts
    _forecasts = forecasts


def _serialize_forecast(fc_entry: dict) -> dict:
    data = fc_entry.get("forecast", [])
    for row in data:
        if hasattr(row.get("date"), "isoformat"):
            row["date"] = row["date"].isoformat()
        elif hasattr(row.get("date"), "strftime"):
            row["date"] = str(row["date"])
    return {
        "forecast": data,
        "metrics": fc_entry.get("metrics", {}),
    }


@router.get("/total")
def forecast_total(horizon: int = Query(30, description="7, 30, or 90")):
    key = f"total_{horizon}d"
    fc = _forecasts.get(key, {})
    return _serialize_forecast(fc)


@router.get("/provider/{provider}")
def forecast_provider(provider: str, horizon: int = Query(30)):
    key = f"{provider}_{horizon}d"
    fc = _forecasts.get(key, {})
    return _serialize_forecast(fc)


@router.get("/team/{team}")
def forecast_team(team: str, horizon: int = Query(30)):
    key = f"team_{team}_{horizon}d"
    fc = _forecasts.get(key, {})
    return _serialize_forecast(fc)


@router.get("/keys")
def list_forecast_keys():
    return {"keys": list(_forecasts.keys())}
