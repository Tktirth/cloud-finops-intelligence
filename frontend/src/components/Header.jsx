import { useState, useRef, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { Bell, Search, RefreshCw, X } from 'lucide-react'
import { usePolling } from '../hooks/useApi'
import { getAlertsSummary, getAlerts } from '../services/api'

const PAGE_TITLES = {
  '/': 'Multi-Cloud Overview',
  '/anomalies': 'Anomaly Detection',
  '/forecasts': 'Spend Forecasting',
  '/budgets': 'Budget Management',
  '/alerts': 'Alert Configuration',
}

export default function Header({ onRefresh }) {
  const location = useLocation()
  const { data: summary } = usePolling(getAlertsSummary, [])
  const { data: alerts } = usePolling(getAlerts, [])
  const [showNotifications, setShowNotifications] = useState(false)
  const notifRef = useRef(null)

  const title = PAGE_TITLES[location.pathname] || 'FinOps Intelligence'
  const critical = summary?.critical || 0

  useEffect(() => {
    function handleClickOutside(event) {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifications(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [notifRef]);

  return (
    <header className="header">
      <div>
        <h1 className="header-title">{title}</h1>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
          Real-time AI-powered cloud cost intelligence
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {['aws', 'azure', 'gcp'].map(p => (
          <div key={p} className={`header-pill provider-pill-${p}`}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', display: 'inline-block' }} />
            {p.toUpperCase()}
          </div>
        ))}

        {/* Alert bell */}
        <div style={{ position: 'relative', marginLeft: 4 }} ref={notifRef}>
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', borderRadius: 10, padding: '8px 10px', cursor: 'pointer', color: showNotifications ? 'var(--primary)' : 'var(--text-primary)', display: 'flex', transition: 'all 0.2s' }}
          >
            <Bell size={16} />
          </button>
          
          {critical > 0 && (
            <span style={{
              position: 'absolute', top: -4, right: -4,
              background: 'var(--critical)', color: '#fff',
              fontSize: 10, fontWeight: 800, borderRadius: '50%',
              width: 16, height: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
              pointerEvents: 'none'
            }}>{critical}</span>
          )}

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div style={{
              position: 'absolute', top: '130%', right: 0, width: 340,
              background: 'rgba(20, 20, 30, 0.95)', backdropFilter: 'blur(20px)',
              border: '1px solid var(--glass-border)', borderRadius: 12, padding: 16,
              zIndex: 1000, boxShadow: '0 10px 40px rgba(0,0,0,0.5)',
              display: 'flex', flexDirection: 'column', gap: 12
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: 10 }}>
                 <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Recent Alerts</h3>
                 <button onClick={() => setShowNotifications(false)} style={{ background:'transparent', border:'none', color:'var(--text-muted)', cursor:'pointer' }}><X size={16} /></button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 350, overflowY: 'auto', paddingRight: 4 }}>
                {(alerts || []).slice(0, 6).map((alert, i) => (
                  <div key={i} style={{ 
                    padding: 12, background: 'rgba(255,255,255,0.03)', borderRadius: 8, 
                    borderLeft: `3px solid var(--${alert.severity.toLowerCase()})`,
                    display: 'flex', flexDirection: 'column', gap: 6
                  }}>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: 11, fontWeight: 800, color: `var(--${alert.severity.toLowerCase()})`, background: `rgba(var(--${alert.severity.toLowerCase()}-rgb), 0.1)`, padding: '2px 6px', borderRadius: 4 }}>{alert.severity}</span>
                        <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{alert.timestamp.split('T')[0]}</span>
                     </div>
                     <div style={{ color: 'var(--text-primary)', fontSize: 13, lineHeight: 1.4 }}>{alert.headline}</div>
                     <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>{alert.team} • {alert.service} • {alert.provider.toUpperCase()}</div>
                  </div>
                ))}
                {(!alerts || alerts.length === 0) && (
                   <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0', fontSize: 13 }}>No active alerts</div>
                )}
              </div>
            </div>
          )}
        </div>

        <button
          onClick={onRefresh}
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', borderRadius: 10, padding: '8px 10px', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex', transition: 'all 0.2s' }}
          title="Refresh data"
        >
          <RefreshCw size={16} />
        </button>
      </div>
    </header>
  )
}
