import { useState } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Brush,
  ResponsiveContainer, BarChart, Bar, Legend, PieChart, Pie, Cell
} from 'recharts'
import { usePolling } from '../hooks/useApi'
import { getSpendTimeline, getSpendByProvider, getSpendByCategory } from '../services/api'
import { format, parseISO } from 'date-fns'

const PROVIDER_COLORS = { aws: '#FF9900', azure: '#00A4EF', gcp: '#34A853' }
const CATEGORY_COLORS = { 
  compute: 'var(--accent)', 
  storage: '#F59E0B', 
  database: '#EF4444', 
  networking: '#00A4EF', 
  analytics: 'var(--low)', 
  other: 'var(--text-muted)' 
}

function SpendTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="custom-tooltip">
      <div className="tooltip-label">{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginTop: 4 }}>
          <span style={{ color: p.color, fontSize: 12 }}>{p.name}</span>
          <span className="tooltip-value" style={{ fontSize: 13 }}>${p.value?.toFixed(0)}</span>
        </div>
      ))}
    </div>
  )
}

export function SpendTimeline() {
  const { data, loading } = usePolling(getSpendTimeline, [])

  if (loading || !data) return <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>

  const formatted = data.map(d => ({
    date: format(parseISO(d.date), 'MMM d'),
    cost: Math.round(d.cost_usd),
  })).filter((_, i) => i % 3 === 0) // sample every 3rd day for readability

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={formatted}>
        <defs>
          <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.4} />
            <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
          </linearGradient>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
        <XAxis 
          dataKey="date" 
          tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 600 }} 
          axisLine={false} 
          tickLine={false} 
          dy={10}
        />
        <YAxis 
          tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 600 }} 
          axisLine={false} 
          tickLine={false} 
          tickFormatter={v => `$${(v/1000).toFixed(0)}K`} 
        />
        <Tooltip content={<SpendTooltip />} cursor={{ stroke: 'var(--accent)', strokeWidth: 1, strokeDasharray: '4 4' }} />
        <Area 
          type="monotone" 
          dataKey="cost" 
          stroke="var(--accent)" 
          fill="url(#costGrad)" 
          strokeWidth={3} 
          dot={false}
          style={{ filter: 'url(#glow)' }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function ProviderSpendChart() {
  const { data, loading } = usePolling(getSpendByProvider, [])

  if (loading || !data) return <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>

  // Aggregate by date × provider
  const byDate = {}
  data.forEach(d => {
    const key = format(parseISO(d.date), 'MMM d')
    if (!byDate[key]) byDate[key] = { date: key }
    byDate[key][d.provider] = (byDate[key][d.provider] || 0) + d.cost_usd
  })
  const chartData = Object.values(byDate).filter((_, i) => i % 7 === 0)

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} barCategoryGap="30%">
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
        <Tooltip content={<SpendTooltip />} />
        {Object.entries(PROVIDER_COLORS).map(([p, c]) => (
          <Bar key={p} dataKey={p} stackId="a" fill={c} radius={p === 'gcp' ? [4, 4, 0, 0] : [0, 0, 0, 0]} />
        ))}
        <Legend formatter={(v) => <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{v.toUpperCase()}</span>} verticalAlign="top" height={36} />
        <Brush dataKey="date" height={25} stroke="#8B9BC8" fill="rgba(255,255,255,0.05)" />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function CategoryDonut() {
  const { data, loading } = usePolling(getSpendByCategory, [])

  if (loading || !data) return <div style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div className="spinner" /></div>

  // Aggregate across providers
  const agg = {}
  data.forEach(d => { agg[d.category] = (agg[d.category] || 0) + d.cost_usd })
  const chartData = Object.entries(agg).map(([name, value]) => ({ name, value: Math.round(value) }))
  const total = chartData.reduce((s, d) => s + d.value, 0)

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
      <ResponsiveContainer width={160} height={160}>
        <PieChart>
          <Pie data={chartData} cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={2} dataKey="value">
            {chartData.map((entry, i) => (
              <Cell key={entry.name} fill={CATEGORY_COLORS[entry.name] || '#8B9BC8'} />
            ))}
          </Pie>
          <Tooltip formatter={(v) => [`$${(v / 1000).toFixed(1)}K`, '']} />
        </PieChart>
      </ResponsiveContainer>
      <div style={{ flex: 1 }}>
        {chartData.sort((a, b) => b.value - a.value).map(d => (
          <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: CATEGORY_COLORS[d.name] || '#8B9BC8', flexShrink: 0 }} />
            <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: 1, textTransform: 'capitalize' }}>{d.name}</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{((d.value / total) * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
