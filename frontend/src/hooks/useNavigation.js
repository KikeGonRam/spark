import { useState, useEffect } from 'react'
import { API_BASE } from '../constants'

export function usePathname() {
  const [pathname, setPathname] = useState(window.location.pathname)
  useEffect(() => {
    const onPop = () => setPathname(window.location.pathname)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  return pathname
}

export const navigate = (path) => {
  if (window.location.pathname !== path) {
    window.history.pushState({}, '', path)
    window.dispatchEvent(new PopStateEvent('popstate'))
  }
}

export const apiFetch = (path, options = {}) =>
  fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(localStorage.getItem('barberpro_token') ? { Authorization: `Bearer ${localStorage.getItem('barberpro_token')}` } : {}),
      ...(options.headers || {}),
    },
  })

export const getStoredToken = () => localStorage.getItem('barberpro_token')

export const decodeJwtPayload = (token) => {
  if (!token) return null
  const part = token.split('.')[1]
  if (!part) return null
  try {
    return JSON.parse(atob(part.replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return null
  }
}

export const getStoredUser = () => {
  try {
    const raw = localStorage.getItem('barberpro_user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}
