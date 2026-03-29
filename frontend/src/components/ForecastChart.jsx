import { useState } from 'react'
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Legend
} from 'recharts'
import { usePolling } from '../hooks/useApi'
import { getForecastTotal, getForecastProvider, getForecastTeam } from '../services/api'
import { format } from 'date-fns'

const HORIZONS = [7, 30, 90]
const PROVIDERS = ['aws', 'azure', 'gcp']
const TEAMS = ['platform', 'data-engineering', 'ml-ops', 'frontend', 'devops']

function ForecastTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="custom-tooltip">
      <div className="tooltip-label">{label}</div>
      {payload.map(p => p.value != null && (
        <div key={p.name} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginTop: 4 }}>
          <span style={{ fontSize: 12, color: p.color }}>{p.name}</span>
          <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: 13 }}>${p.value?.toFixed(0)}</span>
        </div>
      ))}
    </div>
  )
}

function ForecastChart({ fetchFn, args, title, color = '#6C63FF', budgetLine = null }) {
  const [horizon, setHorizon] = useState(30)
  const { data, loading } = usePolling(() => fetchFn(...args, horizon), [horizon, ...args])

  const forecast = data?.forecast || []
  const metrics = data?.metrics || {}

  const chartData = forecast.map(d => ({
    date: d.date ? format(new Date(d.date), 'MMM d') : '',
    p50: Math.round(d.p50 || 0),
    p10: Math.round(d.p10 || 0),
    p90: Math.round(d.p90 || 0),
  }))

  return (
    <div className="card" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div>
          <div className="card-title">{title}</div>
          {metrics.prophet_mape != null && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
              Prophet MAPE: {metrics.prophet_mape?.toFixed(1)}% | LGBM MAPE: {metrics.lgbm_mape?.toFixed(1)}%
            </div>
          )}
        </div>
        <div className="tabs" style={{ margin: 0 }}>
          {HORIZONS.map(h => (
            <button key={h} className={`tab-btn ${horizon === h ? 'active' : ''}`} onClick={() => setHorizon(h)}>{h}d</button>
          ))}
        </div>
      </div>

      <div className="forecast-legend">
        <div className="legend-item"><div className="legend-dot" style={{ background: color + '80' }} />P10–P90 Band</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: color }} />P50 (Expected)</div>
        {budgetLine && <div className="legend-item"><div className="legend-dot" style={{ background: 'var(--critical)' }} />Budget</div>}
      </div>

      {loading ? (
        <div style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>
      ) : chartData.length === 0 ? (
        <div style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 13 }}>No forecast data</div>
      ) : (
        <ResponsiveContainer width="100%" height={180}>
          <ComposedChart data={chartData}>
            <defs>
              <linearGradient id={`band-${title}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.15} />
                <stop offset="95%" stopColor={color} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
            <Tooltip content={<ForecastTooltip />} />
            {/* P10-P90 band */}
            <Area dataKey="p90" stroke="none" fill={`url(#band-${title})`} />
            <Area dataKey="p10" stroke="none" fill="var(--bg-primary)" />
            {/* P50 line */}
            <Line dataKey="p50" stroke={color} strokeWidth={2} dot={false} name="P50 (Expected)" />
            {budgetLine && (
              <ReferenceLine y={budgetLine} stroke="var(--critical)" strokeDasharray="6 3" strokeWidth={1.5} label={{ value: 'Budget', fill: 'var(--critical)', fontSize: 11 }} />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

export function TotalForecastChart() {
  return (
    <ForecastChart
      fetchFn={getForecastTotal}
      args={[]}
      title="Total Cloud Spend Forecast"
      color="#6C63FF"
    />
  )
}

const PROVIDER_COLORS = { aws: '#FF9900', azure: '#0089D6', gcp: '#4CAF50' }

export function ProviderForecastChart({ provider }) {
  return (
    <ForecastChart
      fetchFn={getForecastProvider}
      args={[provider]}
      title={`${provider.toUpperCase()} Spend Forecast`}
      color={PROVIDER_COLORS[provider]}
    />
  )
}

export function TeamForecastChart({ team, budgetLine }) {
  const teamColors = { platform: '#6C63FF', 'data-engineering': '#FF9900', 'ml-ops': '#FF3D57', frontend: '#0089D6', devops: '#4CAF50' }
  return (
    <ForecastChart
      fetchFn={getForecastTeam}
      args={[team]}
      title={`${team} Forecast`}
      color={teamColors[team] || '#6C63FF'}
      budgetLine={budgetLine}
    />
  )
}
