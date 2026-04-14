import { useState, useEffect } from 'react'

export function LiveClock() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', minWidth: 100 }}>
      <div style={{ fontSize: 13, fontWeight: 700, fontFamily: 'monospace', color: 'var(--text-primary)' }}>
        {time.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
      </div>
      <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
        {time.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }).toUpperCase()} (UTC)
      </div>
    </div>
  )
}

export function LiveTicker() {
  const [items, setItems] = useState([
    { label: 'AWS EC2', value: '+$0.12', color: 'var(--low)' },
    { label: 'GCP BQ', value: '-$0.05', color: 'var(--critical)' },
    { label: 'AZURE VM', value: '+$0.08', color: 'var(--low)' },
    { label: 'AWS S3', value: '+$0.02', color: 'var(--low)' },
  ])

  useEffect(() => {
    const interval = setInterval(() => {
      const providers = ['AWS', 'AZURE', 'GCP']
      const services = ['EC2', 'S3', 'RDS', 'Lambda', 'VM', 'Blob', 'Cosmos', 'BQ', 'GKE']
      const p = providers[Math.floor(Math.random() * providers.length)]
      const s = services[Math.floor(Math.random() * services.length)]
      const val = (Math.random() * 0.15).toFixed(2)
      const isUp = Math.random() > 0.3
      
      const newItem = {
        label: `${p} ${s}`,
        value: `${isUp ? '+' : '-'}$${val}`,
        color: isUp ? 'var(--low)' : 'var(--critical)'
      }

      setItems(prev => [newItem, ...prev.slice(0, 5)])
    }, 6000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 24, padding: '0 20px', height: 28, background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid var(--glass-border)', overflow: 'hidden' }}>
      <div style={{ fontSize: 10, fontWeight: 800, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'flex', alignItems: 'center', gap: 6 }}>
        <span className="status-dot" style={{ width: 6, height: 6 }} /> LIVE FEED
      </div>
      <div style={{ display: 'flex', gap: 24, animation: 'ticker 30s linear infinite' }}>
        {items.map((item, i) => (
          <div key={i} style={{ display: 'flex', gap: 6, fontSize: 10, fontWeight: 600, whiteSpace: 'nowrap' }}>
            <span style={{ color: 'var(--text-secondary)' }}>{item.label}:</span>
            <span style={{ color: item.color }}>{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
