import { useState, useEffect } from 'react'

/**
 * Fetch data from an async function on mount and when deps change.
 * @param {Function} fn - Async function returning data
 * @param {Array} deps - Dependency array (callers must ensure referential stability)
 */
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading, error }
}

/**
 * Poll an async function at a regular interval.
 * @param {Function} fn - Async function returning data
 * @param {Array} deps - Dependency array (callers must ensure referential stability)
 * @param {number} intervalMs - Polling interval in milliseconds
 */
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading }
}
