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
  const [tickerSlots, setTickerSlots] = useState([
    { label: '$AMZN (AWS)', value: '185.02', change: '+1.2%', color: 'var(--low)', isIndex: true },
    { label: '$MSFT (AZR)', value: '420.15', change: '+0.8%', color: 'var(--low)', isIndex: true },
    { label: '$GOOGL (GCP)', value: '158.42', change: '-0.3%', color: 'var(--critical)', isIndex: true },
    { label: 'AWS EC2', value: '0.12', change: '+', color: 'var(--low)', isIndex: false },
    { label: 'AZURE VM', value: '0.08', change: '+', color: 'var(--low)', isIndex: false },
    { label: 'GCP BQ', value: '0.05', change: '-', color: 'var(--critical)', isIndex: false },
    { label: 'EU-WEST-1', value: 'SYNC', change: 'OK', color: 'var(--low)', isIndex: false },
    { label: 'US-EAST-1', value: 'SYNC', change: 'OK', color: 'var(--low)', isIndex: false },
  ])

  useEffect(() => {
    const interval = setInterval(() => {
      setTickerSlots(prev => prev.map(slot => {
        if (slot.isIndex) {
          // Indices fluctuate less frequently
          if (Math.random() > 0.8) {
            const val = parseFloat(slot.value) + (Math.random() - 0.4)
            const up = Math.random() > 0.4
            return { ...slot, value: val.toFixed(2), change: (up ? '+' : '-') + (Math.random()*0.5).toFixed(1) + '%', color: up ? 'var(--low)' : 'var(--critical)' }
          }
          return slot
        } else {
          // Costs fluctuate more
          const providers = ['AWS', 'AZR', 'GCP']
          const services = ['EC2', 'S3', 'RDS', 'Lambda', 'VM', 'Blob', 'Cosmos', 'BQ', 'GKE']
          const isUp = Math.random() > 0.3
          return {
            ...slot,
            label: slot.label.includes('-') ? slot.label : `${providers[Math.floor(Math.random()*3)]} ${services[Math.floor(Math.random()*9)]}`,
            value: (Math.random() * 0.15).toFixed(2),
            change: isUp ? '+' : '-',
            color: isUp ? 'var(--low)' : 'var(--critical)'
          }
        }
      }))
    }, 4000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{ 
      display: 'flex', alignItems: 'center', gap: 0, padding: 0, height: 28, 
      background: 'rgba(0,0,0,0.6)', borderBottom: '1px solid var(--glass-border)', 
      overflow: 'hidden', position: 'relative', width: '100%' 
    }}>
      {/* Permanent Status Indicator */}
      <div style={{ 
        height: '100%', padding: '0 16px', background: 'var(--bg-primary)', zIndex: 100,
        fontSize: 10, fontWeight: 900, color: 'var(--accent)', textTransform: 'uppercase', 
        letterSpacing: '0.15em', display: 'flex', alignItems: 'center', gap: 6,
        borderRight: '1px solid var(--glass-border)', boxShadow: '8px 0 16px rgba(0,0,0,0.5)'
      }}>
        <span className="status-dot" style={{ width: 6, height: 6 }} /> 
        <span style={{ whiteSpace: 'nowrap' }}>CLOUD TAPE</span>
      </div>

      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 0, 
        animation: 'ticker 60s linear infinite', 
        willChange: 'transform',
        paddingLeft: '10vw' // Buffer for the status indicator
      }}>
        {/* Triple-Buffer for ultra-seamless loop */}
        {[...tickerSlots, ...tickerSlots, ...tickerSlots].map((item, i) => (
          <div 
            key={`${i}-${item.label}`} 
            style={{ 
              display: 'flex', 
              alignItems: 'center',
              gap: 8, 
              fontSize: 10, 
              fontWeight: 800, 
              whiteSpace: 'nowrap',
              width: item.isIndex ? 220 : 180, 
              padding: '0 20px',
              borderRight: '1px solid rgba(255,255,255,0.05)',
              flexShrink: 0,
              transition: 'all 0.5s ease'
            }}
          >
            <span style={{ color: item.isIndex ? 'var(--text-primary)' : 'var(--text-secondary)', opacity: item.isIndex ? 1 : 0.7 }}>
              {item.label}
            </span>
            <span style={{ 
              color: item.color, 
              fontFamily: 'monospace', 
              textShadow: `0 0 10px ${item.color.replace('var(--', 'rgba(0,255,148,0.2')}` 
            }}>
              {item.isIndex ? '$' : '+'}{item.value}
            </span>
            <span style={{ 
              backgroundColor: item.color === 'var(--low)' ? 'rgba(0,255,148,0.1)' : 'rgba(239,68,68,0.1)',
              color: item.color,
              padding: '1px 4px',
              borderRadius: '2px',
              fontSize: 9,
              fontWeight: 900
            }}>
              {item.change}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

