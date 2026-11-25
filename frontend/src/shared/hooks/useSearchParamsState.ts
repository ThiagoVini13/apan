import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

export function useSearchParamsState<K extends string>(keys: readonly K[]) {
  const [searchParams, setSearchParams] = useSearchParams()

  const values = Object.fromEntries(
    keys.map((key) => [key, searchParams.get(key) ?? '']),
  ) as Record<K, string>

  const update = useCallback(
    (changes: Partial<Record<K, string | null | undefined>>, options?: { resetPage?: boolean }) => {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current)
          for (const [key, value] of Object.entries(changes) as [K, string | null | undefined][]) {
            if (value) next.set(key, value)
            else next.delete(key)
          }
          if (options?.resetPage !== false) next.delete('page')
          return next
        },
        { replace: true },
      )
    },
    [setSearchParams],
  )

  return [values, update] as const
}
