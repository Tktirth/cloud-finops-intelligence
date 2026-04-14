import { DollarSign, AlertTriangle, TrendingUp, Server, Users, Cloud } from 'lucide-react'
import { usePolling } from '../hooks/useApi'
import { getOverviewSummary } from '../services/api'
import { AnimatedCounter } from './AnimatedCounter'

const fmtObj = (v) => {
  if (v >= 1e6) return { value: (v / 1e6).toFixed(2), prefix: '$', suffix: 'M' }
  if (v >= 1e3) return { value: (v / 1e3).toFixed(1), prefix: '$', suffix: 'K' }
  return { value: v.toFixed(0), prefix: '$', suffix: '' }
}

function KpiCard({ icon: Icon, iconBg, label, value, change, changeDir, subtitle }) {
  const meta = typeof value === 'number' ? fmtObj(value) : { value, prefix: '', suffix: '' }
  
  return (
    <div className="card kpi-card">
      <div className="kpi-icon" style={{ background: iconBg, boxShadow: 'inset 0 0 10px rgba(255,255,255,0.2)' }}>
        <Icon size={20} color="#fff" />
      </div>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">
        <AnimatedCounter value={meta.value} prefix={meta.prefix} suffix={meta.suffix} />
      </div>
      {change != null && (
        <div className={`kpi-change ${changeDir}`}>
          <span style={{ fontSize: 10 }}>{changeDir === 'up' ? '▲' : '▼'}</span>
          {Math.abs(change)}% <span style={{ opacity: 0.6, fontSize: 10, marginLeft: 2 }}>MoM</span>
        </div>
      )}
      {subtitle && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, fontWeight: 500 }}>{subtitle}</div>}
    </div>
  )
}

export default function KPICards() {
  const { data, loading } = usePolling(getOverviewSummary, [])

  if (loading || !data) {
    return (
      <div className="kpi-grid">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card kpi-card" style={{ opacity: 0.4 }}>
            <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div className="spinner" style={{ width: 24, height: 24, borderWidth: 2 }} />
            </div>
          </div>
        ))}
      </div>
    )
  }

  const changeDir = data.mom_change_pct >= 0 ? 'up' : 'down'

  return (
    <div className="kpi-grid">
      <KpiCard
        icon={DollarSign}
        iconBg="linear-gradient(135deg, #6C63FF, #9B59B6)"
        label="Total 6-Month Spend"
        value={fmt(data.total_spend_6m)}
        change={data.mom_change_pct}
        changeDir={changeDir}
      />
      <KpiCard
        icon={TrendingUp}
        iconBg="linear-gradient(135deg, #0089D6, #0652DD)"
        label="Last 30-Day Spend"
        value={fmt(data.spend_last_30d)}
        subtitle={`Avg $${((data.spend_last_30d || 0) / 30).toFixed(0)}/day`}
      />
      <KpiCard
        icon={AlertTriangle}
        iconBg="linear-gradient(135deg, #FF3D57, #FF6B6B)"
        label="Anomaly Events"
        value={data.anomaly_count}
        subtitle="Labeled anomaly types"
      />
      <KpiCard
        icon={Cloud}
        iconBg="linear-gradient(135deg, #4CAF50, #0F9B8E)"
        label="Cloud Coverage"
        value={`${data.providers_count} Providers`}
        subtitle={`${data.services_count} Services · ${data.teams_count} Teams`}
      />
    </div>
  )
}
