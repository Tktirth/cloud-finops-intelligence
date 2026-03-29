import { usePolling } from '../hooks/useApi'
import { getAlerts, getAlertsSummary } from '../services/api'
import { Bell, AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-react'
import { format } from 'date-fns'

const SEVERITY_ICONS = {
  CRITICAL: <AlertTriangle size={14} color="var(--critical)" />,
  HIGH: <AlertCircle size={14} color="var(--high)" />,
  MEDIUM: <Info size={14} color="var(--medium)" />,
  LOW: <CheckCircle size={14} color="var(--low)" />,
}

const CONFIGURED_RULES = [
  { name: 'Compute Spike Alert', condition: 'Compute cost > 3× 7-day rolling mean', severity: 'CRITICAL', providers: ['aws', 'azure', 'gcp'], enabled: true },
  { name: 'Storage Drift Alert', condition: 'Storage cost trending up > 5% daily for 7 days', severity: 'HIGH', providers: ['gcp', 'azure'], enabled: true },
  { name: 'Egress Blast Alert', condition: 'Networking cost > 5× daily average', severity: 'CRITICAL', providers: ['aws', 'azure', 'gcp'], enabled: true },
  { name: 'Budget 80% Warning', condition: 'Monthly team spend > 80% of budget', severity: 'WARNING', providers: ['all'], enabled: true },
  { name: 'Cross-Service Spike', condition: 'Compute + network spike simultaneously (corr > 0.8)', severity: 'HIGH', providers: ['aws'], enabled: false },
]

export default function Alerts() {
  const { data: alerts, loading } = usePolling(getAlerts, [])
  const { data: summary } = usePolling(getAlertsSummary, [])

  return (
    <div>
      {/* Summary cards */}
      {summary && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          {[
            { label: 'Total Alerts', value: summary.total, color: 'var(--text-primary)' },
            { label: 'Critical', value: summary.critical, color: 'var(--critical)' },
            { label: 'High', value: summary.high, color: 'var(--high)' },
            { label: 'Medium', value: summary.medium, color: 'var(--medium)' },
            { label: 'Low', value: summary.low, color: 'var(--low)' },
          ].map(s => (
            <div key={s.label} className="card" style={{ flex: 1, padding: '14px 18px' }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid-2" style={{ gap: 16 }}>
        {/* Alert feed */}
        <div>
          <div className="section-title">Alert Feed</div>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            {loading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}><div className="spinner" /></div>
            ) : (
              (alerts || []).map((a, i) => (
                <div key={i} style={{
                  display: 'flex', gap: 12, padding: '14px 16px',
                  borderBottom: '1px solid var(--glass-border)',
                  background: a.severity === 'CRITICAL' ? 'rgba(255,61,87,0.04)' : undefined,
                }}>
                  <div style={{ marginTop: 2 }}>{SEVERITY_ICONS[a.severity]}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                      <span className={`anomaly-badge badge-${a.severity}`}>{a.severity}</span>
                      <span className={`anomaly-badge badge-${a.provider}`}>{a.provider?.toUpperCase()}</span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>
                        {a.timestamp ? String(a.timestamp).slice(0, 10) : ''}
                      </span>
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {a.headline}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {a.root_cause}
                    </div>
                    <div style={{ display: 'flex', gap: 12, marginTop: 4 }}>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.service} · {a.team} · {a.environment}</span>
                      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)', marginLeft: 'auto' }}>${a.cost_usd}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Alert rule configuration */}
        <div>
          <div className="section-title">Configured Alert Rules</div>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            {CONFIGURED_RULES.map((rule, i) => (
              <div key={i} style={{
                padding: '16px', borderBottom: '1px solid var(--glass-border)',
                opacity: rule.enabled ? 1 : 0.5,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Bell size={13} color="var(--text-muted)" />
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{rule.name}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span className={`anomaly-badge badge-${rule.severity}`}>{rule.severity}</span>
                    <div style={{
                      width: 32, height: 18, borderRadius: 9,
                      background: rule.enabled ? 'var(--low)' : 'var(--text-muted)',
                      position: 'relative', cursor: 'pointer', transition: 'background 0.2s',
                    }}>
                      <div style={{
                        width: 14, height: 14, borderRadius: '50%', background: '#fff',
                        position: 'absolute', top: 2, left: rule.enabled ? 16 : 2, transition: 'left 0.2s',
                      }} />
                    </div>
                  </div>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>{rule.condition}</div>
                <div style={{ display: 'flex', gap: 4 }}>
                  {rule.providers.map(p => (
                    <span key={p} className={`anomaly-badge badge-${p}`}>{p.toUpperCase()}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
