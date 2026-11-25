import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { queryRoots } from '@/shared/api/query-roots'
import type {
  CalendarDay,
  CalendarDayCreateInput,
  ItemList,
  SchoolYear,
  SchoolYearCreateInput,
  Term,
  TermCreateInput,
} from '@/shared/api/types'
import { http } from '@/shared/lib/http'

export const schoolYearsKeys = {
  all: queryRoots.schoolYears,
  terms: (yearId: string) => [...schoolYearsKeys.all, yearId, 'terms'] as const,
  days: (yearId: string) => [...schoolYearsKeys.all, yearId, 'calendar-days'] as const,
}

export function useTermsOf(yearId: string) {
  return useQuery({
    queryKey: schoolYearsKeys.terms(yearId),
    queryFn: () => http.get<ItemList<Term>>(`school-years/${yearId}/terms`),
    select: (list) => list.items,
  })
}

export function useCalendarDays(yearId: string) {
  return useQuery({
    queryKey: schoolYearsKeys.days(yearId),
    queryFn: () => http.get<ItemList<CalendarDay>>(`school-years/${yearId}/calendar-days`),
    select: (list) => list.items,
  })
}

function useInvalidate() {
  const queryClient = useQueryClient()
  return () =>
    Promise.all(
      [queryRoots.schoolYears, queryRoots.reference, queryRoots.reports, queryRoots.dashboard].map(
        (queryKey) => queryClient.invalidateQueries({ queryKey }),
      ),
    )
}

export function useSaveSchoolYear() {
  const invalidate = useInvalidate()
  return useMutation({
    mutationFn: ({ id, data }: { id?: string; data: SchoolYearCreateInput }) =>
      id
        ? http.patch<SchoolYear>(`school-years/${id}`, data)
        : http.post<SchoolYear>('school-years', data),
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useDeleteSchoolYear() {
  const invalidate = useInvalidate()
  return useMutation({
    mutationFn: (id: string) => http.delete(`school-years/${id}`),
    onSuccess: invalidate,
  })
}

export function useAddTerm(yearId: string) {
  const invalidate = useInvalidate()
  return useMutation({
    mutationFn: (data: TermCreateInput) => http.post<Term>(`school-years/${yearId}/terms`, data),
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useDeleteTerm(yearId: string) {
  const invalidate = useInvalidate()
  return useMutation({
    mutationFn: (termId: string) => http.delete(`school-years/${yearId}/terms/${termId}`),
    onSuccess: invalidate,
  })
}

export function useAddCalendarDay(yearId: string) {
  const invalidate = useInvalidate()
  return useMutation({
    mutationFn: (data: CalendarDayCreateInput) =>
      http.post<CalendarDay>(`school-years/${yearId}/calendar-days`, data),
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useDeleteCalendarDay(yearId: string) {
  const invalidate = useInvalidate()
  return useMutation({
    mutationFn: (dayId: string) => http.delete(`school-years/${yearId}/calendar-days/${dayId}`),
    onSuccess: invalidate,
  })
}
