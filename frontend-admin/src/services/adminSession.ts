export const ADMIN_TOKEN_KEY = 'adminAccessToken'
export const ADMIN_AUTH_NOTICE_KEY = 'adminAuthNotice'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')
let verifiedToken = ''
let verificationPromise: Promise<AdminSessionVerification> | null = null
let redirectInProgress = false

interface JwtPayload {
  exp?: number
}

export interface AdminSessionVerification {
  valid: boolean
  reason?: 'expired' | 'forbidden' | 'unavailable'
}

export function readAdminToken() {
  return localStorage.getItem(ADMIN_TOKEN_KEY)
}

export function clearAdminSession(message?: string) {
  localStorage.removeItem(ADMIN_TOKEN_KEY)
  verifiedToken = ''
  verificationPromise = null
  if (message) sessionStorage.setItem(ADMIN_AUTH_NOTICE_KEY, message)
}

export function saveAdminSession(token: string) {
  localStorage.setItem(ADMIN_TOKEN_KEY, token)
  verifiedToken = token
  redirectInProgress = false
}

export function consumeAdminAuthNotice() {
  const message = sessionStorage.getItem(ADMIN_AUTH_NOTICE_KEY) || ''
  sessionStorage.removeItem(ADMIN_AUTH_NOTICE_KEY)
  return message
}

export function isJwtExpired(token: string, now = Date.now()) {
  try {
    const payloadPart = token.split('.')[1]
    if (!payloadPart) return true
    const normalized = payloadPart.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
    const payload = JSON.parse(atob(padded)) as JwtPayload
    return typeof payload.exp !== 'number' || payload.exp * 1000 <= now
  } catch {
    return true
  }
}

export function hasValidAdminToken() {
  const token = readAdminToken()
  return Boolean(token && !isJwtExpired(token))
}

export async function verifyAdminSession(): Promise<AdminSessionVerification> {
  const token = readAdminToken()
  if (!token || isJwtExpired(token)) return { valid: false, reason: 'expired' }
  if (verifiedToken === token) return { valid: true }
  if (verificationPromise) return verificationPromise

  verificationPromise = (async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (response.status === 401) return { valid: false, reason: 'expired' }
      if (!response.ok) return { valid: true, reason: 'unavailable' }
      const body = await response.json() as {
        data?: { role?: { code?: string } }
      }
      if (body.data?.role?.code !== 'admin') {
        return { valid: false, reason: 'forbidden' }
      }
      verifiedToken = token
      return { valid: true }
    } catch {
      return { valid: true, reason: 'unavailable' }
    } finally {
      verificationPromise = null
    }
  })()
  return verificationPromise
}

export function redirectToAdminLogin(message: string) {
  clearAdminSession(message)
  if (redirectInProgress || window.location.pathname === '/login') return
  redirectInProgress = true
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
  window.location.replace(`/login?redirect=${encodeURIComponent(current)}`)
}
