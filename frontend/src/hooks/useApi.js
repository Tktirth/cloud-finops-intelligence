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

export function usePolling(fn, deps = [], intervalMs = 30000) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let isMounted = true;
    const fetch = () => {
      fn().then(res => {
        if (isMounted) setData(res);
      }).catch(console.error).finally(() => {
        if (isMounted) setLoading(false);
      })
    }
    fetch()
    const interval = setInterval(fetch, intervalMs)
    return () => {
      isMounted = false;
      clearInterval(interval)
    }
  }, deps)

  return { data, loading }
}
