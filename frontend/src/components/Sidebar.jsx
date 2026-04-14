import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, AlertTriangle, TrendingUp, DollarSign,
  Bell, Activity, Cloud, Zap, Loader
} from 'lucide-react'
import { usePolling } from '../hooks/useApi'
import { getAlertsSummary, getMLStatus } from '../services/api'
import { soundEngine } from '../services/soundEngine'

const NAV = [
  { section: 'OPERATIONS', items: [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/anomalies', label: 'Anomalies', icon: AlertTriangle, badge: true },
    { to: '/forecasts', label: 'Forecasts', icon: TrendingUp },
  ]},
  { section: 'FINANCIAL', items: [
    { to: '/budgets', label: 'Budgets', icon: DollarSign },
    { to: '/alerts', label: 'Alerts', icon: Bell, badge: true },
  ]},
]

export default function Sidebar() {
  const location = useLocation()
  const { data: alertsSummary } = usePolling(getAlertsSummary, [])
  const { data: mlStatus } = usePolling(getMLStatus, [], 5000)

  const pipelineReady = mlStatus?.status === 'Completed Successfully'
  const pipelineError = !!mlStatus?.error
  const statusColor = pipelineError ? 'var(--critical)' : pipelineReady ? 'var(--low)' : 'var(--medium)'
  const statusBg = pipelineError ? 'rgba(239, 68, 68, 0.05)' : pipelineReady ? 'rgba(0, 255, 148, 0.05)' : 'rgba(251, 191, 36, 0.05)'
  const statusBorder = pipelineError ? 'rgba(239, 68, 68, 0.15)' : pipelineReady ? 'rgba(0, 255, 148, 0.15)' : 'rgba(251, 191, 36, 0.15)'
  const statusText = pipelineError ? 'Pipeline Error' : pipelineReady ? 'ML Engine Live' : (mlStatus?.status || 'Connecting...')

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'var(--gradient-blue)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 12px var(--accent-glow)'
          }}>
            <Cloud size={18} color="#fff" />
          </div>
          <div>
            <div className="logo-text">FinIntel Pro</div>
            <div className="logo-sub">QUANTUM COST ENGINE</div>
          </div>
        </div>

        {/* Live Status — connected to real pipeline */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 14, padding: '7px 10px', background: statusBg, borderRadius: 8, border: `1px solid ${statusBorder}` }}>
          {pipelineReady ? <div className="status-dot" style={{ background: 'var(--low)', boxShadow: '0 0 8px var(--low)' }} /> : <Loader size={11} color={statusColor} style={{ animation: 'spin 1.5s linear infinite' }} />}
          <span style={{ fontSize: 10, color: statusColor, fontWeight: 700, letterSpacing: '0.05em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>{statusText.toUpperCase()}</span>
          <Zap size={11} color={statusColor} style={{ flexShrink: 0, opacity: 0.8 }} />
        </div>
        {pipelineReady && mlStatus?.data_end && (
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4, paddingLeft: 2 }}>
            Data: {mlStatus.data_start} → {mlStatus.data_end}
          </div>
        )}
      </div>

      <nav className="sidebar-nav">
        {NAV.map(section => (
          <div key={section.section}>
            <div className="nav-section-label">{section.section}</div>
            {section.items.map(item => {
              const Icon = item.icon
              const critical = alertsSummary?.critical || 0
              const isActive = location.pathname === item.to || (item.to !== '/' && location.pathname.startsWith(item.to))
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={`nav-item ${isActive ? 'active' : ''}`}
                  onClick={() => soundEngine.playTransition()}
                >
                  <Icon size={16} />
                  {item.label}
                  {item.badge && critical > 0 && (
                    <span className="nav-badge">{critical}</span>
                  )}
                </NavLink>
              )
            })}
          </div>
        ))}
      </nav>

      {/* Bottom: Provider pills */}
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--glass-border)' }}>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Connected Providers</div>
        {['aws', 'azure', 'gcp'].map(p => (
          <div key={p} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '5px 0' }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: p === 'aws' ? 'var(--aws)' : p === 'azure' ? 'var(--azure)' : 'var(--gcp)', boxShadow: `0 0 6px ${p === 'aws' ? 'var(--aws)' : p === 'azure' ? 'var(--azure)' : 'var(--gcp)'}` }} />
            <span style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>{p === 'aws' ? 'Amazon Web Services' : p === 'azure' ? 'Microsoft Azure' : 'Google Cloud'}</span>
            <span style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--low)', fontWeight: 600 }}>●</span>
          </div>
        ))}
      </div>
    </aside>
  )
}
