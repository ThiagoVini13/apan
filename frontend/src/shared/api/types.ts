import type { components } from './schema'

type Schemas = components['schemas']

export type Page<T> = { items: T[]; total: number; page: number; pageSize: number }
export type ItemList<T> = { items: T[]; total: number }

export type Role = Schemas['Role']
export type Shift = Schemas['Shift']
export type AttendanceStatus = Schemas['AttendanceStatus']
export type Relationship = Schemas['Relationship']
export type CalendarDayKind = Schemas['CalendarDayKind']
export type EnrollmentStatus = Schemas['EnrollmentStatus']
export type ExportFormat = Schemas['ExportFormat']

export type Me = Schemas['MeRead']
export type TokenResponse = Schemas['TokenRead']
export type LoginInput = Schemas['LoginIn']
export type PasswordChangeInput = Schemas['PasswordChangeIn']
export type PasswordResetInput = Schemas['PasswordResetIn']

export type User = Schemas['UserRead']
export type UserCreateInput = Schemas['UserCreate']
export type UserUpdateInput = Schemas['UserUpdate']

export type SchoolYear = Schemas['SchoolYearRead']
export type SchoolYearCreateInput = Schemas['SchoolYearCreate']
export type SchoolYearUpdateInput = Schemas['SchoolYearUpdate']
export type Term = Schemas['TermRead']
export type TermCreateInput = Schemas['TermCreate']
export type CalendarDay = Schemas['CalendarDayRead']
export type CalendarDayCreateInput = Schemas['CalendarDayCreate']

export type Subject = Schemas['SubjectRead']
export type SubjectCreateInput = Schemas['SubjectCreate']
export type SubjectUpdateInput = Schemas['SubjectUpdate']

export type SchoolClass = Schemas['SchoolClassRead']
export type SchoolClassCreateInput = Schemas['SchoolClassCreate']
export type SchoolClassUpdateInput = Schemas['SchoolClassUpdate']
export type SubjectTeacher = Schemas['SubjectTeacherRead']
export type SubjectTeachersInput = Schemas['SubjectTeachersReplace']

export type Student = Schemas['StudentRead']
export type StudentDetail = Schemas['StudentDetail']
export type StudentCreateInput = Schemas['StudentCreate']
export type StudentUpdateInput = Schemas['StudentUpdate']
export type Guardian = Schemas['GuardianRead']
export type GuardianCreateInput = Schemas['GuardianCreate']
export type GuardianUpdateInput = Schemas['GuardianUpdate']

export type Enrollment = Schemas['EnrollmentRead']
export type EnrollmentTransferInput = Schemas['EnrollmentTransfer']

export type RollCallSheet = Schemas['RollCallSheet']
export type SheetStudent = Schemas['SheetStudent']
export type RollCall = Schemas['RollCallRead']
export type RollCallUpsertInput = Schemas['RollCallUpsert']

export type AttendanceSummary = Schemas['AttendanceSummary']
export type StudentReportRow = Schemas['StudentReportRow']
export type ClassReportRow = Schemas['ClassReportRow']

export type DashboardToday = Schemas['DashboardToday']
export type PendingRollCall = Schemas['PendingRollCall']
export type AtRiskStudent = Schemas['AtRiskStudent']

export type AuditLog = Schemas['AuditLogRead']
