import { useState, useEffect } from 'react'

export function useApi(fn, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    fn()
      .then(d => { setData(d); setError(null) })
      .catch(e => setError(e?.message || 'API Error'))
      .finally(() => setLoading(false))
  }, deps)

  return { data, loading, error }
}

export function usePolling(fn, intervalMs = 30000, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetch = () => fn().then(setData).catch(console.error).finally(() => setLoading(false))
    fetch()
    const interval = setInterval(fetch, intervalMs)
    return () => clearInterval(interval)
  }, deps)

  return { data, loading }
}
