export type Shift = 'morning' | 'afternoon' | 'evening'
export type AttendanceStatus = 'present' | 'absent'

// ---- Classes ----

export interface SchoolClass {
  id: string
  name: string
  grade: string
  section: string
  shift: Shift
  year: number
  studentCount: number
}

export interface SchoolClassList {
  items: SchoolClass[]
  total: number
}

// ---- Subjects ----

export interface Subject {
  id: string
  code: string
  name: string
}

// ---- Students ----

export interface Student {
  id: string
  fullName: string
  enrollmentNumber: string
  classId: string
  birthDate: string | null
  isActive: boolean
  attendanceRate: number | null
}

export interface StudentList {
  items: Student[]
  total: number
}

export interface StudentCreateInput {
  fullName: string
  enrollmentNumber: string
  classId: string
  birthDate?: string
  isActive?: boolean
}

// ---- Roll calls ----

export interface AttendanceRecord {
  id: string
  studentId: string
  status: AttendanceStatus
}

export interface RollCall {
  id: string
  classId: string
  subjectId: string
  lessonDate: string
  notes: string | null
  createdAt: string
  updatedAt: string
  attendances: AttendanceRecord[]
}

export interface RollCallList {
  items: RollCall[]
  total: number
}

export interface RollCallUpsertInput {
  classId: string
  subjectId: string
  lessonDate: string
  notes?: string
  attendances: { studentId: string; status: AttendanceStatus }[]
}

// ---- Dashboard ----

export interface DashboardToday {
  totalStudents: number
  totalClasses: number
  rollCallsCompleted: number
  presenceRate: number
  classesWithPendingRollCall: SchoolClass[]
  lowAttendanceStudents: Student[]
}
