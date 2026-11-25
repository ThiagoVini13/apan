import { QueryClientProvider, type QueryClient } from '@tanstack/react-query'
import { useEffect, useState, type ReactNode } from 'react'
import { onUnauthorized } from '@/shared/lib/http'
import { sessionKeys } from '@/shared/session/session'
import { Toaster } from '@/shared/ui/toast'
import { applyTheme, useThemeStore } from '@/stores/theme.store'
import { createQueryClient } from './query-client'

function ThemeSync() {
  const theme = useThemeStore((state) => state.theme)
  useEffect(() => {
    applyTheme(theme)
    if (theme !== 'system' || typeof window.matchMedia !== 'function') return
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const listener = () => applyTheme('system')
    media.addEventListener('change', listener)
    return () => media.removeEventListener('change', listener)
  }, [theme])
  return null
}

type ProvidersProps = { children: ReactNode; queryClient?: QueryClient }

export function Providers({ children, queryClient }: ProvidersProps) {
  const [client] = useState(() => queryClient ?? createQueryClient())

  useEffect(() => {
    onUnauthorized(() => client.setQueryData(sessionKeys.current(), null))
  }, [client])

  return (
    <QueryClientProvider client={client}>
      <ThemeSync />
      {children}
      <Toaster />
    </QueryClientProvider>
  )
}
