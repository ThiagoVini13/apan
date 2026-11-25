import { useQuery, useQueryClient } from '@tanstack/react-query'
import type { Me, Role, TokenResponse } from '@/shared/api/types'
import { refreshAccessToken, tokenStore } from '@/shared/lib/auth-token'
import { http } from '@/shared/lib/http'

export const sessionKeys = {
  all: ['session'] as const,
  current: () => [...sessionKeys.all, 'current'] as const,
}

async function fetchSession(): Promise<Me | null> {
  if (!tokenStore.get() && !(await refreshAccessToken())) return null
  try {
    return await http.get<Me>('auth/me')
  } catch {
    return null
  }
}

export function useSession() {
  return useQuery({
    queryKey: sessionKeys.current(),
    queryFn: fetchSession,
    staleTime: Infinity,
    retry: false,
  })
}

export function useCurrentUser(): Me {
  const { data } = useSession()
  if (!data) throw new Error('useCurrentUser must be used inside RequireAuth')
  return data
}

export function useHasRole(...roles: Role[]): boolean {
  const { data } = useSession()
  return !!data && roles.includes(data.role)
}

export function useStartSession() {
  const queryClient = useQueryClient()
  return (tokens: TokenResponse) => {
    tokenStore.set(tokens.accessToken)
    queryClient.setQueryData(sessionKeys.current(), tokens.user)
  }
}

export function useEndSession() {
  const queryClient = useQueryClient()
  return async () => {
    await http.post('auth/logout', undefined, { skipAuthRefresh: true }).catch(() => undefined)
    tokenStore.set(null)
    queryClient.clear()
    queryClient.setQueryData(sessionKeys.current(), null)
  }
}
