import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, AlertTriangle, TrendingUp, DollarSign,
  Bell, Activity, Cloud, Zap
} from 'lucide-react'
import { usePolling } from '../hooks/useApi'
import { getAlertsSummary } from '../services/api'

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

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 10,
            background: 'linear-gradient(135deg, #6C63FF, #9B59B6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Cloud size={18} color="#fff" />
          </div>
          <div>
            <div className="logo-text">FinOps AI</div>
            <div className="logo-sub">Intelligence Platform</div>
          </div>
        </div>

        {/* Live Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 12, padding: '6px 10px', background: 'rgba(6,214,160,0.08)', borderRadius: 8, border: '1px solid rgba(6,214,160,0.2)' }}>
          <div className="status-dot" />
          <span style={{ fontSize: 11, color: 'var(--low)', fontWeight: 600 }}>ML Pipeline Active</span>
          <Zap size={11} color="var(--low)" style={{ marginLeft: 'auto' }} />
        </div>
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
