import { queryRoots } from '@/shared/api/query-roots'
import type { ReportParams } from '../types'

export const reportsKeys = {
  all: queryRoots.reports,
  summary: (params: ReportParams) => [...reportsKeys.all, 'summary', params] as const,
  students: (params: ReportParams) => [...reportsKeys.all, 'students', params] as const,
  byClass: (params: ReportParams) => [...reportsKeys.all, 'by-class', params] as const,
  terms: (schoolYearId: string) => [...reportsKeys.all, 'terms', schoolYearId] as const,
}
