import { useMutation, useQueryClient } from '@tanstack/react-query'
import { queryRoots } from '@/shared/api/query-roots'
import type { Subject, SubjectCreateInput } from '@/shared/api/types'
import { http } from '@/shared/lib/http'

export function useSaveSubject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id?: string; data: SubjectCreateInput }) =>
      id ? http.patch<Subject>(`subjects/${id}`, data) : http.post<Subject>('subjects', data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryRoots.reference }),
    meta: { handlesErrors: true },
  })
}

export function useDeleteSubject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => http.delete(`subjects/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryRoots.reference }),
  })
}
