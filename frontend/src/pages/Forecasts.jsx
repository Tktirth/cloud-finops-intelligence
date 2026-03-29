import { TotalForecastChart, ProviderForecastChart, TeamForecastChart } from '../components/ForecastChart'

const TEAMS_BUDGETS = {
  platform: 45000,
  'data-engineering': 38000,
  'ml-ops': 30000,
  frontend: 22000,
  devops: 15000,
}

export default function Forecasts() {
  return (
    <div>
      {/* Methodology callout */}
      <div className="card" style={{ padding: 20, marginBottom: 20, background: 'rgba(108,99,255,0.06)', borderColor: 'rgba(108,99,255,0.2)' }}>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)', marginBottom: 6 }}>🔮 Ensemble Forecasting Engine</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Combines Facebook Prophet (trend + weekly seasonality) and LightGBM quantile regression (13 lag features).
              Best model per segment selected via 30-day backtest MAPE. Output: P10/P50/P90 confidence intervals.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            {[['Prophet', 'var(--aws)'], ['LightGBM', 'var(--accent)'], ['Ensemble', 'var(--low)']].map(([name, color]) => (
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

      {/* Team forecasts */}
      <div>
        <div className="section-title">By Team (with Budget Lines)</div>
        <div className="grid-2">
          {Object.entries(TEAMS_BUDGETS).map(([team, budget]) => (
            <TeamForecastChart key={team} team={team} budgetLine={budget / 30} />
          ))}
        </div>
      </div>
    </div>
  )
}
