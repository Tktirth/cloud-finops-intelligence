"""
Alert Engine
Configurable alert rules with severity scoring and budget breach prediction.
Uses dynamic quarterly budgets from the data generator for full sync.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import norm

# Import dynamic budget functions from the data generator
from data.generator import get_team_monthly_budget, PROVIDER_MONTHLY_BUDGETS, TEAMS


def _get_current_team_budgets(reference_date) -> dict:
    """Get team budgets for the current quarter based on reference date."""
    return {team: get_team_monthly_budget(team, reference_date) for team in TEAMS}

ALERT_SEVERITY_THRESHOLDS = {
    "CRITICAL": 75,
    "HIGH": 50,
    "MEDIUM": 25,
    "LOW": 0,
}


def generate_alerts(anomalies_df: pd.DataFrame) -> list:
    """Convert detected anomalies to alert objects with configurable severity."""
    alerts = []
    for _, row in anomalies_df.iterrows():
        severity = row.get("severity_label", "LOW")
        score = row.get("severity_score", 0)

        # Only generate alerts for MEDIUM+ severity
        if score < 25:
            continue

        chain = row.get("causal_chain", {})
        if not isinstance(chain, dict):
            chain = {}

        alerts.append({
            "alert_id": f"ALT-{row['date'].strftime('%Y%m%d') if hasattr(row['date'], 'strftime') else str(row['date'])[:10].replace('-', '')}-{row['resource_key'][:8].replace('/', '')}",
            "timestamp": str(row["date"]),
            "provider": row.get("provider", ""),
            "service": row.get("service", ""),
            "team": row.get("team", ""),
            "environment": row.get("environment", ""),
            "resource_key": row.get("resource_key", ""),
            "severity": severity,
            "severity_score": score,
            "cost_usd": round(float(row.get("cost_usd", 0)), 2),
            "headline": chain.get("headline", f"Anomalous cost detected in {row.get('service', '')}"),
            "root_cause": chain.get("root_cause", "Under investigation"),
            "detector_votes": int(row.get("detector_votes", 1)),
            "anomaly_type": row.get("type_label", "Unknown"),
            "acknowledged": False,
            "resolved": False,
        })

    return sorted(alerts, key=lambda x: (-x["severity_score"], x["timestamp"]))


def predict_budget_breach(daily_df: pd.DataFrame, forecasts: dict) -> list:
    """
    Predict budget breach probability and estimated date for each team.
    Uses forecast P90 (worst case) and P50 (expected).
    """
    breaches = []
    df_dates = pd.to_datetime(daily_df["date"])
    current_date = df_dates.max()
    month_start = current_date.replace(day=1)

    # Current month spend so far per team
    month_mask = df_dates >= month_start
    month_spending = daily_df[month_mask].groupby("team")["cost_usd"].sum()
    # And overall provider
    month_provider_spending = daily_df[month_mask].groupby("provider")["cost_usd"].sum()

    # Days remaining in month
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    days_remaining = (next_month - current_date).days

    for team, budget in _get_current_team_budgets(current_date).items():
        spent = float(month_spending.get(team, 0))
        remaining_budget = budget - spent

        # Get 30-day team forecast
        fc_key = f"team_{team}_30d"
        fc = forecasts.get(fc_key, {})
        fc_data = fc.get("forecast", []) if isinstance(fc, dict) else []

        if fc_data:
            fc_df = pd.DataFrame(fc_data).head(days_remaining)
            forecasted_spend = fc_df["p50"].sum() if "p50" in fc_df else 0
            forecasted_spend_p90 = fc_df["p90"].sum() if "p90" in fc_df else forecasted_spend * 1.15

            total_expected = spent + forecasted_spend
            total_worst = spent + forecasted_spend_p90

            # Breach probability: probability that total spend > budget
            # Use normal distribution approximation
            spread = max(total_worst - total_expected, 1)
            std_approx = spread / 1.28  # P90 is ~1.28 sigma
            breach_prob = float(1 - norm.cdf(budget, loc=total_expected, scale=std_approx))
            breach_prob = round(min(max(breach_prob, 0), 1), 4)

            # Estimated breach date (simple linear extrapolation)
            daily_rate = forecasted_spend / max(days_remaining, 1)
            days_to_breach = int(remaining_budget / daily_rate) if daily_rate > 0 else 999
            breach_date = (current_date + timedelta(days=min(days_to_breach, 365))).date().isoformat()
        else:
            total_expected = spent * 1.1
            total_worst = spent * 1.25
            breach_prob = min(spent / budget, 1.0)
            breach_date = None

        status = "OVER_BUDGET" if spent >= budget else (
            "AT_RISK" if breach_prob > 0.7 else
            "WARNING" if breach_prob > 0.4 else "ON_TRACK"
        )

        breaches.append({
            "team": team,
            "type": "team",
            "monthly_budget_usd": budget,
            "spent_so_far_usd": round(spent, 2),
            "budget_utilization_pct": round(spent / budget * 100, 1),
            "forecasted_total_usd": round(total_expected, 2),
            "forecasted_worst_usd": round(total_worst, 2),
            "breach_probability": breach_prob,
            "estimated_breach_date": breach_date,
            "status": status,
        })

    for provider, budget in PROVIDER_MONTHLY_BUDGETS.items():
        spent = float(month_provider_spending.get(provider, 0))
        remaining_budget = budget - spent

        fc_key = f"{provider}_30d"
        fc = forecasts.get(fc_key, {})
        fc_data = fc.get("forecast", []) if isinstance(fc, dict) else []

        if fc_data:
            fc_df = pd.DataFrame(fc_data).head(days_remaining)
            forecasted_spend = fc_df["p50"].sum() if "p50" in fc_df else 0
            forecasted_p90 = fc_df["p90"].sum() if "p90" in fc_df else forecasted_spend * 1.1
            total_expected = spent + forecasted_spend
            total_worst = spent + forecasted_p90
            spread = max(total_worst - total_expected, 1)
            std_approx = spread / 1.28
            breach_prob = float(1 - norm.cdf(budget, loc=total_expected, scale=std_approx))
            breach_prob = round(min(max(breach_prob, 0), 1), 4)
        else:
            total_expected = spent * 1.1
            breach_prob = min(spent / budget, 1.0)

        status = "OVER_BUDGET" if spent >= budget else (
            "AT_RISK" if breach_prob > 0.7 else
            "WARNING" if breach_prob > 0.4 else "ON_TRACK"
        )

        breaches.append({
            "team": provider,
            "type": "provider",
            "monthly_budget_usd": budget,
            "spent_so_far_usd": round(spent, 2),
            "budget_utilization_pct": round(spent / budget * 100, 1),
            "forecasted_total_usd": round(total_expected, 2),
            "forecasted_worst_usd": round(total_expected * 1.1, 2),
            "breach_probability": breach_prob,
            "estimated_breach_date": None,
            "status": status,
        })

    return sorted(breaches, key=lambda x: -x["breach_probability"])
