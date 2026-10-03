import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/lib/api'
import type { StudentList, Student, StudentCreateInput } from '@/shared/types'

export const studentsKeys = {
  all: ['students'] as const,
  lists: () => [...studentsKeys.all, 'list'] as const,
  list: (filters: { q?: string; classId?: string }) =>
    [...studentsKeys.lists(), filters] as const,
  detail: (id: string) => [...studentsKeys.all, 'detail', id] as const,
}

export function useStudents(filters: { q?: string; classId?: string } = {}) {
  const params = new URLSearchParams()
  if (filters.q) params.set('q', filters.q)
  if (filters.classId) params.set('class_id', filters.classId)
  const qs = params.toString() ? `?${params.toString()}` : ''

  return useQuery({
    queryKey: studentsKeys.list(filters),
    queryFn: () => api.get<StudentList>(`/students${qs}`),
    placeholderData: (prev) => prev,
  })
}

export function useStudent(id: string) {
  return useQuery({
    queryKey: studentsKeys.detail(id),
    queryFn: () => api.get<Student>(`/students/${id}`),
    enabled: Boolean(id),
  })
}

export function useCreateStudent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: StudentCreateInput) => api.post<Student>('/students', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: studentsKeys.all })
    },
  })
}
