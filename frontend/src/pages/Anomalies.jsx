import { useState, Fragment } from 'react'
import { usePolling } from '../hooks/useApi'
import { getAnomalies, getAnomaliesByType, getAnomalyMetrics } from '../services/api'
import { format, parseISO } from 'date-fns'
import RootCausePanel from '../components/RootCausePanel'
import { Filter } from 'lucide-react'

const PROVIDERS = ['', 'aws', 'azure', 'gcp']
const SEVERITIES = ['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
const TEAMS = ['', 'platform', 'data-engineering', 'ml-ops', 'frontend', 'devops']

function SelectFilter({ label, value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
        borderRadius: 8, padding: '7px 12px', color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer',
      }}
    >
      {options.map(o => <option key={o || 'all'} value={o}>{o || `All ${label}s`}</option>)}
    </select>
  )
}

export default function Anomalies() {
  const [provider, setProvider] = useState('')
  const [severity, setSeverity] = useState('')
  const [team, setTeam] = useState('')
  const [selected, setSelected] = useState(null)
  const [limit] = useState(100)

  const params = {}
  if (provider) params.provider = provider
  if (severity) params.severity = severity
  if (team) params.team = team
  params.limit = limit

  const { data, loading } = usePolling(() => getAnomalies(params), [provider, severity, team])
  const { data: byType } = usePolling(getAnomaliesByType, [])
  const { data: metrics } = usePolling(getAnomalyMetrics, [])

  return (
    <div>
      {/* Metrics row */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        {[
          { label: 'F1 Score', value: (((metrics?.f1 || 0) * 100).toFixed(1)) + '%', color: 'var(--low)' },
          { label: 'Precision', value: (((metrics?.precision || 0) * 100).toFixed(1)) + '%', color: 'var(--accent)' },
          { label: 'Recall', value: (((metrics?.recall || 0) * 100).toFixed(1)) + '%', color: 'var(--aws)' },
          { label: 'True Positives', value: metrics?.true_positives || 0, color: 'var(--low)' },
          { label: 'False Positives', value: metrics?.false_positives || 0, color: 'var(--critical)' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding: '12px 18px', flex: 1, minWidth: 110 }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: m.color }}>{m.value}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>{m.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ gap: 16, marginBottom: 20 }}>
        {/* Anomalies by type */}
        <div className="card" style={{ padding: 20 }}>
          <div className="card-title" style={{ marginBottom: 14 }}>Anomalies by Type</div>
          {byType ? byType.map(t => (
            <div key={t.type_label} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500, marginBottom: 3 }}>{t.type_label}</div>
                <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2 }}>
                  <div style={{ height: '100%', background: 'var(--gradient-blue)', borderRadius: 2, width: `${Math.min((t.count || 0) * 15, 100)}%` }} />
                </div>
              </div>
              <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', minWidth: 24 }}>{t.count || 0}</span>
            </div>
          )) : (
            <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>Waiting for detection engine...</div>
          )}
        </div>

        {/* Filters summary */}
        <div className="card" style={{ padding: 20 }}>
          <div className="card-title" style={{ marginBottom: 14 }}>Detection Methodology</div>
          {[
            { name: 'Statistical (STL + GESD)', desc: 'Seasonal decomposition + Z-score for sudden spikes and outliers', color: 'var(--aws)' },
            { name: 'ML (Isolation Forest + SVM)', desc: 'Ensemble on 13 engineered time-series features', color: 'var(--accent)' },
            { name: 'Deep Learning (LSTM AE)', desc: 'Reconstruction error with 14-day sequence windows', color: 'var(--gcp)' },
          ].map(m => (
            <div key={m.name} style={{ display: 'flex', gap: 12, padding: '10px 0', borderBottom: '1px solid var(--glass-border)' }}>
              <div style={{ width: 3, background: m.color, borderRadius: 3, flexShrink: 0, alignSelf: 'stretch' }} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{m.name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{m.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
        <Filter size={15} color="var(--text-muted)" />
        <SelectFilter label="Provider" value={provider} onChange={setProvider} options={PROVIDERS} />
        <SelectFilter label="Severity" value={severity} onChange={setSeverity} options={SEVERITIES} />
        <SelectFilter label="Team" value={team} onChange={setTeam} options={TEAMS} />
        <span style={{ marginLeft: 'auto', fontSize: 13, color: 'var(--text-muted)' }}>
          {data?.length || 0} anomalies
        </span>
      </div>

      {/* Anomaly table */}
      <div className="card" style={{ padding: '0 0 4px' }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}><div className="spinner" /></div>
        ) : (
          <>
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Severity</th>
                    <th>Provider</th>
                    <th>Service</th>
                    <th>Team / Env</th>
                    <th>Cost</th>
                    <th>Type</th>
                    <th>Detectors</th>
                  </tr>
                </thead>
                <tbody>
                  {(data || []).map((a, i) => (
                    <Fragment key={i}>
                      <tr
                        onClick={() => setSelected(selected?.date === a.date && selected?.resource_key === a.resource_key ? null : a)}
                        style={{ cursor: 'pointer', background: selected?.resource_key === a.resource_key && selected?.date === a.date ? 'rgba(108,99,255,0.07)' : undefined }}
                      >
                        <td className="mono" style={{ fontSize: 12 }}>{a.date ? String(a.date).slice(0, 10) : ''}</td>
                        <td><span className={`anomaly-badge badge-${a.severity_label}`}>{a.severity_label}</span></td>
                        <td><span className={`anomaly-badge badge-${a.provider}`}>{a.provider?.toUpperCase()}</span></td>
                        <td style={{ fontSize: 13 }}>{a.service}</td>
                        <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{a.team} / {a.environment}</td>
                        <td className="mono" style={{ fontWeight: 600 }}>${a.cost_usd?.toFixed(0)}</td>
                        <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{a.type_label || 'detected'}</td>
                        <td>
                          <div style={{ display: 'flex', gap: 4 }}>
                            {a.is_stat_anomaly && <span title="Statistical" style={{ fontSize: 10, padding: '1px 6px', background: 'rgba(255,153,0,0.1)', color: 'var(--aws)', borderRadius: 4, border: '1px solid rgba(255,153,0,0.2)' }}>Stat</span>}
                            {a.is_ml_anomaly && <span title="ML" style={{ fontSize: 10, padding: '1px 6px', background: 'rgba(108,99,255,0.1)', color: 'var(--accent)', borderRadius: 4, border: '1px solid rgba(108,99,255,0.2)' }}>ML</span>}
                            {a.is_dl_anomaly && <span title="Deep Learning" style={{ fontSize: 10, padding: '1px 6px', background: 'rgba(76,175,80,0.1)', color: 'var(--gcp)', borderRadius: 4, border: '1px solid rgba(76,175,80,0.2)' }}>DL</span>}
                          </div>
                        </td>
                      </tr>
                      {selected?.resource_key === a.resource_key && selected?.date === a.date && (
                        <tr key={`detail-${i}`}>
                          <td colSpan={8} style={{ padding: '0 16px 16px' }}>
                            <RootCausePanel anomaly={a} onClose={() => setSelected(null)} />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
