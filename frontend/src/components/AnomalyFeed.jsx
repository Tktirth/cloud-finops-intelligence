import { useState } from 'react'
import { AlertTriangle, ChevronRight, Cpu } from 'lucide-react'
import { usePolling } from '../hooks/useApi'
import { getRecentAnomalies } from '../services/api'
import { format, parseISO } from 'date-fns'
import RootCausePanel from './RootCausePanel'

function AnomalyBadge({ severity }) {
  return <span className={`anomaly-badge badge-${severity}`}>{severity}</span>
}
function ProviderBadge({ provider }) {
  return <span className={`anomaly-badge badge-${provider}`}>{provider?.toUpperCase()}</span>
}

export default function AnomalyFeed({ compact = false }) {
  const { data, loading } = usePolling(getRecentAnomalies, [])
  const [selected, setSelected] = useState(null)

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: 24 }}><div className="spinner" /></div>
  if (!data?.length) return <div style={{ padding: 20, color: 'var(--text-muted)', textAlign: 'center', fontSize: 13 }}>No anomalies detected</div>

  return (
    <div>
      {data.map((a, i) => {
        const key = a.resource_key || `${a.provider}/${a.service}/${a.team}/${a.environment}`
        const isSelected = selected?.resource_key === a.resource_key && selected?.date === a.date
        return (
          <div
            key={i}
            className={`anomaly-item ${isSelected ? 'selected' : ''}`}
            onClick={() => setSelected(isSelected ? null : a)}
          >
            <div className={`anomaly-severity-bar severity-${a.severity_label || 'LOW'}`} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, flexWrap: 'wrap' }}>
                <AnomalyBadge severity={a.severity_label || 'LOW'} />
                <ProviderBadge provider={a.provider} />
                <span className="anomaly-badge" style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)', border: '1px solid var(--glass-border)' }}>
                  {a.service}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>
                  {a.date ? format(parseISO(String(a.date).slice(0, 10)), 'MMM d') : ''}
                </span>
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 3, color: 'var(--text-primary)' }}>
                {a.anomaly_description || 'Cost anomaly detected'}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {a.team} / {a.environment}
                </span>
                <span style={{ fontSize: 12, fontWeight: 700, color: a.severity_label === 'CRITICAL' ? 'var(--critical)' : 'var(--text-primary)' }}>
                  ${a.cost_usd?.toFixed(0)}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  {(a.severity_score || 0).toFixed(0)} / 100 severity
                </span>
              </div>
            </div>
            <ChevronRight size={14} color="var(--text-muted)" style={{ transform: isSelected ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }} />
          </div>
        )
      })}

      {selected && (
        <RootCausePanel anomaly={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}
