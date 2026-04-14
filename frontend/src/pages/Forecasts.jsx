import { TotalForecastChart, ProviderForecastChart, TeamForecastChart } from '../components/ForecastChart'
import { usePolling } from '../hooks/useApi'
import { getBudgets } from '../services/api'

export default function Forecasts() {
  // Pull budgets from backend (dynamic quarterly values) instead of hardcoding
  const { data: budgets } = usePolling(getBudgets, [])

  // Build team budget map from live backend data
  const teamBudgets = {}
  if (budgets) {
    budgets.filter(b => b.type === 'team').forEach(b => {
      teamBudgets[b.team] = b.monthly_budget_usd
    })
  }

  return (
    <div>
      {/* Methodology callout */}
      <div className="card" style={{ padding: 20, marginBottom: 20, background: 'rgba(108,99,255,0.06)', borderColor: 'rgba(108,99,255,0.2)' }}>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)', marginBottom: 6 }}>🔮 Ensemble Forecasting Engine</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Uses GradientBoosting quantile regression (13 lag features + calendar features) for P10/P50/P90 confidence intervals.
              Best model per segment selected via 30-day backtest MAPE. Forecasts project from today's actual spend data.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            {[['GBM Quantile', 'var(--accent)'], ['P50 Expected', 'var(--low)'], ['P10–P90 Band', 'var(--text-muted)']].map(([name, color]) => (
              <div key={name} style={{ textAlign: 'center', padding: '10px 16px', background: 'rgba(255,255,255,0.03)', borderRadius: 10, border: `1px solid ${color}30` }}>
                <div style={{ fontSize: 14, fontWeight: 700, color }}>{name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Model</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Total forecast */}
      <div style={{ marginBottom: 20 }}>
        <div className="section-title">Total Cloud Spend</div>
        <TotalForecastChart />
      </div>

      {/* Provider forecasts */}
      <div style={{ marginBottom: 20 }}>
        <div className="section-title">By Cloud Provider</div>
        <div className="grid-3">
          {['aws', 'azure', 'gcp'].map(p => (
            <ProviderForecastChart key={p} provider={p} />
          ))}
        </div>
      </div>

      {/* Team forecasts with live budget lines */}
      <div>
        <div className="section-title">By Team (with Budget Lines)</div>
        <div className="grid-2">
          {Object.entries(teamBudgets).length > 0
            ? Object.entries(teamBudgets).map(([team, budget]) => (
                <TeamForecastChart key={team} team={team} budgetLine={budget / 30} />
              ))
            : <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: 20 }}>Loading team budgets...</div>
          }
        </div>
      </div>
    </div>
  )
}
