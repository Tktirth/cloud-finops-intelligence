import { usePolling } from '../hooks/useApi'
import { getBudgets } from '../services/api'
import { AlertTriangle, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

const STATUS_ICONS = {
  ON_TRACK: <CheckCircle size={14} color="var(--low)" />,
  WARNING: <AlertCircle size={14} color="var(--medium)" />,
  AT_RISK: <AlertTriangle size={14} color="var(--high)" />,
  OVER_BUDGET: <XCircle size={14} color="var(--critical)" />,
}

const STATUS_BAR_COLORS = {
  ON_TRACK: 'var(--low)',
  WARNING: 'var(--medium)',
  AT_RISK: 'var(--high)',
  OVER_BUDGET: 'var(--critical)',
}

const fmtK = v => v >= 1000 ? `$${(v / 1000).toFixed(0)}K` : `$${v?.toFixed(0)}`

export default function BudgetTracker({ filter = 'all' }) {
  const { data, loading } = usePolling(getBudgets, [])

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: 24 }}><div className="spinner" /></div>
  if (!data?.length) return <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>No budget data</div>

  const filtered = filter === 'all' ? data : data.filter(b => b.type === filter)

  return (
    <div>
      {filtered.map((b, i) => {
        const pct = Math.min(b.budget_utilization_pct || 0, 100)
        const barColor = STATUS_BAR_COLORS[b.status] || 'var(--accent)'
        const breachPct = Math.round((b.breach_probability || 0) * 100)

        return (
          <div key={i} className="budget-item">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {STATUS_ICONS[b.status] || null}
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                  {b.team}
                </span>
                {b.type === 'provider' && (
                  <span className={`anomaly-badge badge-${b.team}`}>{b.team.toUpperCase()}</span>
                )}
              </div>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Breach:</span>
                <span style={{
                  fontSize: 12, fontWeight: 700,
                  color: breachPct > 70 ? 'var(--critical)' : breachPct > 40 ? 'var(--high)' : 'var(--low)',
                }}>{breachPct}%</span>
              </div>
            </div>

            <div className="budget-bar-track">
              <div className="budget-bar-fill" style={{ width: `${pct}%`, background: barColor }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                {fmtK(b.spent_so_far_usd)} spent of {fmtK(b.monthly_budget_usd)}
              </span>
              <span className={`status-${b.status}`} style={{ fontSize: 11, fontWeight: 700 }}>
                {b.status?.replace(/_/g, ' ')}
              </span>
            </div>

            {b.breach_probability > 0.4 && b.estimated_breach_date && (
              <div style={{ marginTop: 6, padding: '5px 8px', background: 'rgba(255,61,87,0.06)', borderRadius: 6, border: '1px solid rgba(255,61,87,0.15)' }}>
                <span style={{ fontSize: 11, color: 'var(--critical)' }}>
                  ⚠ Projected breach: {b.estimated_breach_date}
                </span>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
