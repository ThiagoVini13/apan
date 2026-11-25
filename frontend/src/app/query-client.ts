import { MutationCache, QueryClient } from '@tanstack/react-query'
import { errorMessage } from '@/shared/lib/errors'
import { ApiError } from '@/shared/lib/http'
import { notify } from '@/shared/ui/toast.store'

declare module '@tanstack/react-query' {
  interface Register {
    mutationMeta: { handlesErrors?: boolean }
  }
}

function shouldRetry(failureCount: number, error: unknown) {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false
  return failureCount < 1
}

export function createQueryClient() {
  return new QueryClient({
    mutationCache: new MutationCache({
      onError: (error, _variables, _context, mutation) => {
        if (mutation.meta?.handlesErrors) return
        if (error instanceof ApiError && error.status === 401) return
        notify.error(errorMessage(error))
      },
    }),
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: shouldRetry,
        refetchOnWindowFocus: false,
      },
      mutations: { retry: false },
    },
  })
}
