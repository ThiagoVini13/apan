import { env } from './env'

type Listener = (token: string | null) => void

let accessToken: string | null = null
const listeners = new Set<Listener>()

export const CSRF_HEADERS = { 'X-Requested-With': 'XMLHttpRequest' } as const

export const tokenStore = {
  get: () => accessToken,
  set(token: string | null) {
    accessToken = token
    listeners.forEach((listener) => listener(token))
  },
  subscribe(listener: Listener) {
    listeners.add(listener)
    return () => {
      listeners.delete(listener)
    }
  },
}

type RefreshResult = { accessToken: string } | null

let inFlight: Promise<RefreshResult> | null = null

async function requestRefresh(): Promise<RefreshResult> {
  const response = await fetch(
    `${globalThis.location?.origin ?? ''}${env.apiPrefix}/auth/refresh`,
    {
      method: 'POST',
      credentials: 'same-origin',
      headers: CSRF_HEADERS,
    },
  ).catch(() => null)
  if (!response?.ok) return null
  const body = (await response.json()) as { accessToken: string }
  return { accessToken: body.accessToken }
}

/**
 * Renews the access token with the refresh cookie. Concurrent callers share one request,
 * and tabs take turns through the Web Locks API: the server revokes the whole session if
 * a rotated refresh token is presented twice.
 */
export function refreshAccessToken(): Promise<boolean> {
  inFlight ??= (async () => {
    const locks = typeof navigator !== 'undefined' ? navigator.locks : undefined
    const result = locks
      ? await locks.request('apan-auth-refresh', requestRefresh)
      : await requestRefresh()
    tokenStore.set(result?.accessToken ?? null)
    return result
  })().finally(() => {
    inFlight = null
  })
  return inFlight.then((result) => result !== null)
}
