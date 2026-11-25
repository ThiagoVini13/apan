import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { queryRoots } from '@/shared/api/query-roots'
import type {
  GuardianCreateInput,
  GuardianUpdateInput,
  StudentCreateInput,
  StudentUpdateInput,
} from '@/shared/api/types'
import type { StudentsFilters } from '../types'
import { studentsApi } from './students.api'
import { studentsKeys } from './students.keys'

export function useStudents(filters: StudentsFilters) {
  return useQuery({
    queryKey: studentsKeys.list(filters),
    queryFn: () => studentsApi.list(filters),
    placeholderData: keepPreviousData,
  })
}

export function useStudent(id: string | undefined) {
  return useQuery({
    queryKey: studentsKeys.detail(id ?? ''),
    queryFn: () => studentsApi.get(id as string),
    enabled: !!id,
  })
}

export function useStudentRates(range: { from: string; to: string } | null) {
  return useQuery({
    queryKey: studentsKeys.rates(range?.from ?? '', range?.to ?? ''),
    queryFn: () => studentsApi.rates(range!.from, range!.to),
    enabled: range !== null,
    select: (list) => new Map(list.items.map((row) => [row.studentId, row.attendanceRate])),
  })
}

function useInvalidateStudents() {
  const queryClient = useQueryClient()
  return () =>
    Promise.all(
      [queryRoots.students, queryRoots.reference, queryRoots.dashboard].map((queryKey) =>
        queryClient.invalidateQueries({ queryKey }),
      ),
    )
}

export function useCreateStudent() {
  const invalidate = useInvalidateStudents()
  return useMutation({
    mutationFn: (data: StudentCreateInput) => studentsApi.create(data),
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useUpdateStudent(id: string) {
  const invalidate = useInvalidateStudents()
  return useMutation({
    mutationFn: (data: StudentUpdateInput) => studentsApi.update(id, data),
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useArchiveStudent(id: string) {
  const invalidate = useInvalidateStudents()
  return useMutation({ mutationFn: () => studentsApi.archive(id), onSuccess: invalidate })
}

export function useTransferStudent() {
  const invalidate = useInvalidateStudents()
  return useMutation({
    mutationFn: ({
      enrollmentId,
      classId,
      transferOn,
    }: {
      enrollmentId: string
      classId: string
      transferOn: string
    }) => studentsApi.transfer(enrollmentId, classId, transferOn),
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useEnrollStudent() {
  const invalidate = useInvalidateStudents()
  return useMutation({
    mutationFn: ({ studentId, classId }: { studentId: string; classId: string }) =>
      studentsApi.enroll(studentId, classId),
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useAddGuardian(studentId: string) {
  const invalidate = useInvalidateStudents()
  return useMutation({
    mutationFn: (data: GuardianCreateInput) => studentsApi.addGuardian(studentId, data),
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useUpdateGuardian(studentId: string) {
  const invalidate = useInvalidateStudents()
  return useMutation({
    mutationFn: ({ guardianId, data }: { guardianId: string; data: GuardianUpdateInput }) =>
      studentsApi.updateGuardian(studentId, guardianId, data),
    onSuccess: invalidate,
  })
}

export function useDeleteGuardian(studentId: string) {
  const invalidate = useInvalidateStudents()
  return useMutation({
    mutationFn: (guardianId: string) => studentsApi.deleteGuardian(studentId, guardianId),
    onSuccess: invalidate,
  })
}
