"""Budgets and Alerts routers."""

from fastapi import APIRouter

budgets_router = APIRouter(prefix="/api/budgets", tags=["budgets"])
alerts_router = APIRouter(prefix="/api/alerts", tags=["alerts"])

_budget_data = None
_alert_data = None


def set_budget_data(data: list):
    global _budget_data
    _budget_data = data


def set_alert_data(data: list):
    global _alert_data
    _alert_data = data


@budgets_router.get("/")
def list_budgets():
    return _budget_data or []


@budgets_router.get("/teams")
def team_budgets():
    return [b for b in (_budget_data or []) if b.get("type") == "team"]


@budgets_router.get("/providers")
def provider_budgets():
    return [b for b in (_budget_data or []) if b.get("type") == "provider"]


@alerts_router.get("/")
def list_alerts(limit: int = 50):
    data = _alert_data or []
    return data[:limit]


@alerts_router.get("/critical")
def critical_alerts():
    return [a for a in (_alert_data or []) if a.get("severity") == "CRITICAL"]


@alerts_router.get("/summary")
def alerts_summary():
    data = _alert_data or []
    return {
        "total": len(data),
        "critical": sum(1 for a in data if a.get("severity") == "CRITICAL"),
        "high": sum(1 for a in data if a.get("severity") == "HIGH"),
        "medium": sum(1 for a in data if a.get("severity") == "MEDIUM"),
        "low": sum(1 for a in data if a.get("severity") == "LOW"),
    }
