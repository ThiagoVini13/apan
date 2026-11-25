import { useMutation, useQueryClient } from '@tanstack/react-query'
import { queryRoots } from '@/shared/api/query-roots'
import type {
  ItemList,
  SchoolClass,
  SchoolClassCreateInput,
  SchoolClassUpdateInput,
  SubjectTeacher,
  SubjectTeachersInput,
} from '@/shared/api/types'
import { http } from '@/shared/lib/http'

export const classesApi = {
  create: (data: SchoolClassCreateInput) => http.post<SchoolClass>('classes', data),
  update: (id: string, data: SchoolClassUpdateInput) =>
    http.patch<SchoolClass>(`classes/${id}`, data),
  archive: (id: string) => http.post<SchoolClass>(`classes/${id}/archive`),
  replaceSubjectTeachers: (id: string, data: SubjectTeachersInput) =>
    http.put<ItemList<SubjectTeacher>>(`classes/${id}/subject-teachers`, data),
}

function useInvalidateClasses() {
  const queryClient = useQueryClient()
  return () =>
    Promise.all(
      [queryRoots.reference, queryRoots.dashboard].map((queryKey) =>
        queryClient.invalidateQueries({ queryKey }),
      ),
    )
}

export function useSaveClass() {
  const invalidate = useInvalidateClasses()
  return useMutation({
    mutationFn: ({ id, data }: { id?: string; data: SchoolClassCreateInput }) => {
      if (!id) return classesApi.create(data)
      const { schoolYearId, ...changes } = data
      return classesApi.update(id, changes)
    },
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useArchiveClass() {
  const invalidate = useInvalidateClasses()
  return useMutation({ mutationFn: classesApi.archive, onSuccess: invalidate })
}

export function useReplaceSubjectTeachers(classId: string) {
  const invalidate = useInvalidateClasses()
  return useMutation({
    mutationFn: (data: SubjectTeachersInput) => classesApi.replaceSubjectTeachers(classId, data),
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}
