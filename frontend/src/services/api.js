import axios from 'axios'
import config from '../config'

const api = axios.create({ baseURL: config.apiUrl })

export const getOverviewSummary = () => api.get('/overview/summary').then(r => r.data)
export const getSpendTimeline = () => api.get('/overview/spend-timeline').then(r => r.data)
export const getSpendByProvider = () => api.get('/overview/spend-by-provider').then(r => r.data)
export const getSpendByService = () => api.get('/overview/spend-by-service').then(r => r.data)
export const getSpendByCategory = () => api.get('/overview/spend-by-category').then(r => r.data)
export const getHeatmap = () => api.get('/overview/heatmap').then(r => r.data)

export const getAnomalies = (params = {}) => api.get('/anomalies/', { params }).then(r => r.data)
export const getRecentAnomalies = (limit = 8) => api.get(`/anomalies/recent?limit=${limit}`).then(r => r.data)
export const getAnomalyMetrics = () => api.get('/anomalies/metrics').then(r => r.data)
export const getAnomaliesByType = () => api.get('/anomalies/by-type').then(r => r.data)

export const getForecastTotal = (horizon = 30) => api.get(`/forecasts/total?horizon=${horizon}`).then(r => r.data)
export const getForecastProvider = (provider, horizon = 30) => api.get(`/forecasts/provider/${provider}?horizon=${horizon}`).then(r => r.data)
export const getForecastTeam = (team, horizon = 30) => api.get(`/forecasts/team/${team}?horizon=${horizon}`).then(r => r.data)

export const getBudgets = () => api.get('/budgets/').then(r => r.data)
export const getTeamBudgets = () => api.get('/budgets/teams').then(r => r.data)
export const getProviderBudgets = () => api.get('/budgets/providers').then(r => r.data)

export const getAlerts = (limit = 50) => api.get(`/alerts/?limit=${limit}`).then(r => r.data)
export const getCriticalAlerts = () => api.get('/alerts/critical').then(r => r.data)
export const getAlertsSummary = () => api.get('/alerts/summary').then(r => r.data)

export const getMLStatus = () => api.get('/debug-ml').then(r => r.data)

export default api
