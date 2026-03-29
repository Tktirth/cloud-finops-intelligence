"""Overview router — KPI cards and multi-cloud spend summary."""

from fastapi import APIRouter
import pandas as pd

router = APIRouter(prefix="/api/overview", tags=["overview"])

_store = None

def set_store(store):
    global _store
    _store = store


@router.get("/summary")
def get_summary():
    return _store.summary


@router.get("/spend-by-provider")
def spend_by_provider():
    df = _store.by_provider_service.groupby(["date", "provider"])["cost_usd"].sum().reset_index()
    df["date"] = df["date"].astype(str)
    return df.to_dict(orient="records")


@router.get("/spend-by-service")
def spend_by_service():
    df = _store.by_provider_service.groupby(["provider", "service"])["cost_usd"].sum().reset_index()
    return df.sort_values("cost_usd", ascending=False).to_dict(orient="records")


@router.get("/spend-by-category")
def spend_by_category():
    df = _store.full.groupby(["provider", "category"])["cost_usd"].sum().reset_index()
    return df.sort_values("cost_usd", ascending=False).to_dict(orient="records")


@router.get("/spend-timeline")
def spend_timeline():
    df = _store.full.groupby("date")["cost_usd"].sum().reset_index()
    df["date"] = df["date"].astype(str)
    return df.to_dict(orient="records")


@router.get("/heatmap")
def spend_heatmap():
    """Provider × Service spend matrix for heatmap visualization."""
    df = _store.full.groupby(["provider", "service"])["cost_usd"].sum().reset_index()
    return df.to_dict(orient="records")
