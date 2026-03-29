import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import Anomalies from './pages/Anomalies'
import Forecasts from './pages/Forecasts'
import Budgets from './pages/Budgets'
import Alerts from './pages/Alerts'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <div className="main-area">
          <Header onRefresh={() => window.location.reload()} />
          <main className="page-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/anomalies" element={<Anomalies />} />
              <Route path="/forecasts" element={<Forecasts />} />
              <Route path="/budgets" element={<Budgets />} />
              <Route path="/alerts" element={<Alerts />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}
