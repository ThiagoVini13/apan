import type {
  Enrollment,
  Guardian,
  GuardianCreateInput,
  GuardianUpdateInput,
  ItemList,
  Page,
  Student,
  StudentCreateInput,
  StudentDetail,
  StudentReportRow,
  StudentUpdateInput,
} from '@/shared/api/types'
import { DEFAULT_PAGE_SIZE } from '@/shared/lib/constants'
import { http } from '@/shared/lib/http'
import type { StudentsFilters } from '../types'

export const studentsApi = {
  list: (filters: StudentsFilters) =>
    http.get<Page<Student>>('students', { ...filters, pageSize: DEFAULT_PAGE_SIZE }),
  get: (id: string) => http.get<StudentDetail>(`students/${id}`),
  create: (data: StudentCreateInput) => http.post<StudentDetail>('students', data),
  update: (id: string, data: StudentUpdateInput) =>
    http.patch<StudentDetail>(`students/${id}`, data),
  archive: (id: string) => http.post<StudentDetail>(`students/${id}/archive`),
  addGuardian: (studentId: string, data: GuardianCreateInput) =>
    http.post<Guardian>(`students/${studentId}/guardians`, data),
  updateGuardian: (studentId: string, guardianId: string, data: GuardianUpdateInput) =>
    http.patch<Guardian>(`students/${studentId}/guardians/${guardianId}`, data),
  deleteGuardian: (studentId: string, guardianId: string) =>
    http.delete(`students/${studentId}/guardians/${guardianId}`),
  transfer: (enrollmentId: string, classId: string, transferOn: string) =>
    http.post<Enrollment>(`enrollments/${enrollmentId}/transfer`, { classId, transferOn }),
  enroll: (studentId: string, classId: string) =>
    http.post<Enrollment>('enrollments', { studentId, classId }),
  rates: (from: string, to: string, classId?: string) =>
    http.get<ItemList<StudentReportRow>>('reports/attendance/students', { from, to, classId }),
}
