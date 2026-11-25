import { useQuery } from '@tanstack/react-query'
import { http } from '@/shared/lib/http'
import { queryRoots } from './query-roots'
import type { ItemList, Page, SchoolClass, SchoolYear, Subject, SubjectTeacher } from './types'

const REFERENCE_STALE_TIME = 10 * 60 * 1000
const ALL = { pageSize: 100 }

export const referenceKeys = {
  all: queryRoots.reference,
  classes: (filters: ClassFilters = {}) => [...referenceKeys.all, 'classes', filters] as const,
  subjects: () => [...referenceKeys.all, 'subjects'] as const,
  schoolYears: () => [...referenceKeys.all, 'school-years'] as const,
  subjectTeachers: (classId: string) =>
    [...referenceKeys.all, 'subject-teachers', classId] as const,
}

export type ClassFilters = { schoolYearId?: string; isActive?: boolean }

export function useClassOptions(filters: ClassFilters = { isActive: true }) {
  return useQuery({
    queryKey: referenceKeys.classes(filters),
    queryFn: () => http.get<Page<SchoolClass>>('classes', { ...ALL, ...filters }),
    staleTime: REFERENCE_STALE_TIME,
    select: (page) => page.items,
  })
}

export function useSubjectOptions() {
  return useQuery({
    queryKey: referenceKeys.subjects(),
    queryFn: () => http.get<Page<Subject>>('subjects', ALL),
    staleTime: REFERENCE_STALE_TIME,
    select: (page) => page.items,
  })
}

export function useSchoolYears() {
  return useQuery({
    queryKey: referenceKeys.schoolYears(),
    queryFn: () => http.get<Page<SchoolYear>>('school-years', ALL),
    staleTime: REFERENCE_STALE_TIME,
    select: (page) => page.items,
  })
}

export function useCurrentSchoolYear() {
  const query = useSchoolYears()
  return { ...query, data: query.data?.find((year) => year.isCurrent) ?? null }
}

export function useSubjectTeachers(classId: string | undefined) {
  return useQuery({
    queryKey: referenceKeys.subjectTeachers(classId ?? ''),
    queryFn: () => http.get<ItemList<SubjectTeacher>>(`classes/${classId}/subject-teachers`),
    enabled: !!classId,
    staleTime: REFERENCE_STALE_TIME,
    select: (list) => list.items,
  })
}
