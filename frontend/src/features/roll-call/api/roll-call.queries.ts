import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/lib/api'
import type { RollCallList, RollCall, RollCallUpsertInput } from '@/shared/types'
import { dashboardKeys } from '@/features/dashboard/api/dashboard.queries'
import { studentsKeys } from '@/features/students/api/students.queries'

export const rollCallsKeys = {
  all: ['roll-calls'] as const,
  list: (filters: { classId?: string; date?: string }) =>
    [...rollCallsKeys.all, 'list', filters] as const,
  detail: (id: string) => [...rollCallsKeys.all, 'detail', id] as const,
}

export function useRollCalls(filters: { classId?: string; date?: string } = {}) {
  const params = new URLSearchParams()
  if (filters.classId) params.set('class_id', filters.classId)
  if (filters.date) params.set('date', filters.date)
  const qs = params.toString() ? `?${params.toString()}` : ''

  return useQuery({
    queryKey: rollCallsKeys.list(filters),
    queryFn: () => api.get<RollCallList>(`/roll-calls${qs}`),
    enabled: Boolean(filters.classId),
  })
}

export function useSaveRollCall() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: RollCallUpsertInput) => api.put<RollCall>('/roll-calls', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: rollCallsKeys.all })
      qc.invalidateQueries({ queryKey: dashboardKeys.today })
      qc.invalidateQueries({ queryKey: studentsKeys.all })
    },
  })
}
