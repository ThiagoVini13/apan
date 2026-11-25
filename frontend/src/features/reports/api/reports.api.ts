import type {
  AttendanceSummary,
  ClassReportRow,
  ExportFormat,
  ItemList,
  StudentReportRow,
  Term,
} from '@/shared/api/types'
import { http } from '@/shared/lib/http'
import type { ReportParams } from '../types'

function query(params: ReportParams) {
  return {
    from: params.from,
    to: params.to,
    classId: params.classId,
    subjectId: params.subjectId,
  }
}

export const reportsApi = {
  summary: (params: ReportParams) =>
    http.get<AttendanceSummary>('reports/attendance/summary', query(params)),
  students: (params: ReportParams) =>
    http.get<ItemList<StudentReportRow>>('reports/attendance/students', query(params)),
  byClass: (params: ReportParams) =>
    http.get<ItemList<ClassReportRow>>('reports/attendance/by-class', query(params)),
  export: (params: ReportParams, format: ExportFormat) =>
    http.blob('reports/attendance/export', { ...query(params), format }),
  terms: (schoolYearId: string) => http.get<ItemList<Term>>(`school-years/${schoolYearId}/terms`),
}
