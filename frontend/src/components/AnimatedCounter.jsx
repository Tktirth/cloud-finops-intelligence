import { useState, useEffect, useRef } from 'react'

export function AnimatedCounter({ value, duration = 1000, prefix = '', suffix = '' }) {
  const [count, setCount] = useState(0)
  const countRef = useRef(0)
  const startTimeRef = useRef(null)

  useEffect(() => {
    // Extract numeric value from string if needed ($2.5M -> 2.5)
    const numericValue = typeof value === 'number' ? value : parseFloat(value.replace(/[^0-9.]/g, ''))
    const startValue = countRef.current
    startTimeRef.current = null

    const animate = (timestamp) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp
      const progress = Math.min((timestamp - startTimeRef.current) / duration, 1)
      
      // Easing function (outQuart)
      const easedProgress = 1 - Math.pow(1 - progress, 4)
      const currentCount = startValue + (numericValue - startValue) * easedProgress
      
      setCount(currentCount)
      countRef.current = currentCount

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [value, duration])

  // Format back to same style as input
  let displayValue = ''
  if (typeof value === 'string' && value.includes('M')) {
    displayValue = `${prefix}${count.toFixed(2)}M${suffix}`
  } else if (typeof value === 'string' && value.includes('K')) {
    displayValue = `${prefix}${count.toFixed(1)}K${suffix}`
  } else {
    displayValue = `${prefix}${count.toFixed(0)}${suffix}`
  }

  return <span>{displayValue}</span>
}
