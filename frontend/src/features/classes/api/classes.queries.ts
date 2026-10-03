import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/lib/api'
import type { SchoolClassList } from '@/shared/types'

export const classesKeys = {
  all: ['classes'] as const,
  list: () => [...classesKeys.all, 'list'] as const,
}

export function useClasses() {
  return useQuery({
    queryKey: classesKeys.list(),
    queryFn: () => api.get<SchoolClassList>('/classes'),
    staleTime: 10 * 60 * 1000,
  })
}
