import BudgetTracker from '../components/BudgetTracker'

export default function Budgets() {
  return (
    <div>
      <div className="card" style={{ padding: 20, marginBottom: 20, background: 'rgba(255,61,87,0.04)', borderColor: 'rgba(255,61,87,0.15)' }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--critical)', marginBottom: 4 }}>💰 Budget Breach Prediction</div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.6 }}>
          Breach probability computed from ensemble forecast distribution (P50 = expected, P90 = worst case).
          Uses normal distribution approximation to calculate P(total spend &gt; budget) for each team and provider.
          Estimated breach date derived from linear extrapolation of daily forecasted spend.
        </div>
      </div>

      <div className="grid-2" style={{ gap: 20 }}>
        <div>
          <div className="section-title">Team Budgets</div>
          <div className="card" style={{ padding: 20 }}>
            <BudgetTracker filter="team" />
          </div>
        </div>
        <div>
          <div className="section-title">Provider Budgets</div>
          <div className="card" style={{ padding: 20 }}>
            <BudgetTracker filter="provider" />
          </div>
        </div>
      </div>
    </div>
  )
}
