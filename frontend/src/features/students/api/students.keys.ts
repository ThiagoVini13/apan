import { queryRoots } from '@/shared/api/query-roots'
import type { StudentsFilters } from '../types'

export const studentsKeys = {
  all: queryRoots.students,
  lists: () => [...studentsKeys.all, 'list'] as const,
  list: (filters: StudentsFilters) => [...studentsKeys.lists(), filters] as const,
  details: () => [...studentsKeys.all, 'detail'] as const,
  detail: (id: string) => [...studentsKeys.details(), id] as const,
  rates: (from: string, to: string, classId?: string) =>
    [...studentsKeys.all, 'rates', { from, to, classId }] as const,
}
