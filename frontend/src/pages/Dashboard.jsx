import KPICards from '../components/KPICards'
import { SpendTimeline, ProviderSpendChart, CategoryDonut } from '../components/MultiCloudCharts'
import AnomalyFeed from '../components/AnomalyFeed'
import BudgetTracker from '../components/BudgetTracker'
import { TotalForecastChart } from '../components/ForecastChart'
import { usePolling } from '../hooks/useApi'
import { getAnomalyMetrics } from '../services/api'

function MetricBubble({ label, value, color }) {
  return (
    <div style={{ textAlign: 'center', padding: '12px 16px', background: 'rgba(255,255,255,0.03)', borderRadius: 10, border: '1px solid var(--glass-border)' }}>
      <div style={{ fontSize: 22, fontWeight: 800, color }}>{value}</div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{label}</div>
    </div>
  )
}

export default function Dashboard() {
  const { data: metrics } = usePolling(getAnomalyMetrics, [])

  return (
    <div className="fade-in-up" style={{ animationDelay: '0.1s' }}>
      {/* KPI Row */}
      <KPICards />

      {/* Main grid */}
      <div className="grid-2 fade-in-up" style={{ gap: 16, marginBottom: 16, animationDelay: '0.2s' }}>
        {/* Spend Timeline */}
        <div className="card chart-container">
          <div className="card-title" style={{ marginBottom: 14 }}>Daily Total Spend (6 Months)</div>
          <SpendTimeline />
        </div>

        {/* Provider breakdown */}
        <div className="card chart-container">
          <div className="card-title" style={{ marginBottom: 14 }}>Spend by Cloud Provider</div>
          <ProviderSpendChart />
        </div>
      </div>

      <div className="grid-2" style={{ gap: 16, marginBottom: 16 }}>
        {/* Forecast */}
        <TotalForecastChart />

        {/* Detection metrics + Category donut */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {metrics ? (
            <div className="card" style={{ padding: 20 }}>
              <div className="card-title" style={{ marginBottom: 12 }}>Anomaly Detection Accuracy</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 12 }}>
                <MetricBubble label="F1 Score" value={((metrics.f1 || 0) * 100).toFixed(0) + '%'} color="var(--low)" />
                <MetricBubble label="Precision" value={((metrics.precision || 0) * 100).toFixed(0) + '%'} color="var(--accent)" />
                <MetricBubble label="Recall" value={((metrics.recall || 0) * 100).toFixed(0) + '%'} color="var(--aws)" />
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Stats: {metrics.true_positives || 0} TP · {metrics.false_positives || 0} FP · {metrics.false_negatives || 0} FN</div>
            </div>
          ) : (
            <div className="card" style={{ padding: 20, height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Calculating ML metrics...</div>
            </div>
          )}
          <div className="card" style={{ padding: 20, flex: 1 }}>
            <div className="card-title" style={{ marginBottom: 12 }}>Spend by Category</div>
            <CategoryDonut />
          </div>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid-2" style={{ gap: 16 }}>
        <div className="card" style={{ padding: 20 }}>
          <div className="card-title" style={{ marginBottom: 14 }}>Recent Anomalies</div>
          <AnomalyFeed compact />
        </div>
        <div className="card" style={{ padding: 20 }}>
          <div className="card-title" style={{ marginBottom: 14 }}>Budget Status</div>
          <BudgetTracker filter="team" />
        </div>
      </div>
    </div>
  )
}
