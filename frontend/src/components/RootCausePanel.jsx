import { X, GitBranch, Cpu, BarChart2 } from 'lucide-react'

function ShapBar({ feature, importance, direction, maxImp }) {
  const pct = maxImp > 0 ? (importance / maxImp) * 100 : 0
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace' }}>
          {feature.replace(/_/g, ' ')}
        </span>
        <span style={{ fontSize: 11, color: direction === 'increase' ? 'var(--critical)' : 'var(--low)', fontWeight: 600 }}>
          {direction === 'increase' ? '↑' : '↓'} {(importance * 100).toFixed(2)}
        </span>
      </div>
      <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
        <div
          className="shap-bar"
          style={{
            width: `${pct}%`,
            background: direction === 'increase'
              ? 'linear-gradient(90deg, #FF3D57, #FF8C42)'
              : 'linear-gradient(90deg, #6C63FF, #4CAF50)',
          }}
        />
      </div>
    </div>
  )
}

export default function RootCausePanel({ anomaly, onClose }) {
  const chain = anomaly?.causal_chain
  if (!chain) return null

  const shapFeatures = chain.shap_attribution || []
  const maxImp = Math.max(...shapFeatures.map(f => f.importance || 0), 0.001)

  return (
    <div className="card" style={{ margin: '0 0 12px', padding: 20, borderColor: 'rgba(108,99,255,0.3)', animation: 'slideDown 0.2s ease' }}>
      <style>{`@keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } }`}</style>

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
            🔍 Root Cause Attribution
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{chain.anomaly_id} · {chain.type?.replace(/_/g, ' ')}</div>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 4 }}>
          <X size={16} />
        </button>
      </div>

      {/* Root cause */}
      <div style={{ background: 'rgba(255,61,87,0.08)', border: '1px solid rgba(255,61,87,0.2)', borderRadius: 10, padding: '12px 14px', marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: 'var(--critical)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
          Root Cause
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.6 }}>
          {chain.root_cause}
        </div>
        {chain.cost_impact_usd !== undefined && (
          <div style={{ marginTop: 8, fontSize: 12, color: 'var(--critical)', fontWeight: 600 }}>
            Cost Impact: +${chain.cost_impact_usd?.toFixed(2)}
          </div>
        )}
      </div>

      <div className="grid-2" style={{ gap: 16 }}>
        {/* Causal steps */}
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
            <GitBranch size={12} style={{ display: 'inline', marginRight: 5 }} />Causal Chain
          </div>
          {(chain.causal_steps || []).map((step, i) => (
            <div key={i} className="causal-step">
              <div className="step-num">{i + 1}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, paddingTop: 2 }}>{step}</div>
            </div>
          ))}
        </div>

        {/* SHAP attribution */}
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
            <BarChart2 size={12} style={{ display: 'inline', marginRight: 5 }} />SHAP Feature Attribution
          </div>
          {shapFeatures.length > 0
            ? shapFeatures.slice(0, 6).map((f, i) => (
                <ShapBar key={i} {...f} maxImp={maxImp} />
              ))
            : <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Attribution data unavailable</div>
          }
          <div style={{ marginTop: 10, padding: '8px', background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Contributing services:</div>
            <div style={{ display: 'flex', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
              {(chain.contributing_services || []).map(s => (
                <span key={s} style={{ padding: '2px 8px', background: 'rgba(108,99,255,0.1)', border: '1px solid rgba(108,99,255,0.2)', borderRadius: 6, fontSize: 11, color: 'var(--accent)', fontFamily: 'JetBrains Mono, monospace' }}>{s}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
