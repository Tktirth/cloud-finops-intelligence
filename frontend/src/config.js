/**
 * Global Configuration Environment
 * Professional-grade endpoint management for dev/prod environments.
 */

const env = import.meta.env.MODE || 'development'

const config = {
  development: {
    // Local FastAPI port (default 8000)
    apiUrl: 'http://localhost:8000/api'
  },
  production: {
    // This value should be set in Vercel 'Environment Variables' as VITE_API_URL
    // If not set, it defaults to the specific Render URL provided by the user.
    apiUrl: import.meta.env.VITE_API_URL || 'https://cloud-finops-intelligence-backend.onrender.com/api'
  }
}

const currentConfig = env === 'production' ? config.production : config.development

console.log(`🌐 [Config] Environment: ${env} | API Base: ${currentConfig.apiUrl}`)

export default currentConfig
