import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { queryRoots } from '@/shared/api/query-roots'
import type { SheetParams } from '../types'
import { rollCallApi } from './roll-call.api'
import { rollCallKeys } from './roll-call.keys'

export function useRollCallSheet(params: SheetParams | null) {
  return useQuery({
    queryKey: rollCallKeys.sheet(params ?? { classId: '', subjectId: '', date: '' }),
    queryFn: () => rollCallApi.sheet(params as SheetParams),
    enabled: params !== null,
  })
}

export function useSaveRollCall() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: rollCallApi.save,
    onSuccess: () =>
      Promise.all(
        [queryRoots.rollCalls, queryRoots.dashboard, queryRoots.reports, queryRoots.students].map(
          (queryKey) => queryClient.invalidateQueries({ queryKey }),
        ),
      ),
    meta: { handlesErrors: true },
  })
}
