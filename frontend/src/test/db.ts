import type {
  AttendanceStatus,
  Me,
  RollCallUpsertInput,
  SchoolClass,
  SchoolYear,
  SheetStudent,
  Student,
  Subject,
  SubjectTeacher,
} from '@/shared/api/types'

export const TODAY = new Date().toISOString().slice(0, 10)

export const admin: Me = {
  id: 'user-admin',
  email: 'diretoria@example.com',
  fullName: 'Diretoria APAN',
  role: 'admin',
  mustChangePassword: false,
  permissions: ['users:manage'],
}

export const teacher: Me = {
  id: 'user-teacher',
  email: 'professora@example.com',
  fullName: 'Ana Professora',
  role: 'teacher',
  mustChangePassword: false,
  permissions: ['roll_calls:write_own'],
}

const year: SchoolYear = {
  id: 'year-2026',
  name: '2026',
  startsOn: '2000-01-01',
  endsOn: '2099-12-31',
  isCurrent: true,
}

const subject: Subject = { id: 'subject-math', name: 'Matemática', code: 'MAT' }

const schoolClass: SchoolClass = {
  id: 'class-5a',
  schoolYearId: year.id,
  name: '5º Ano A',
  grade: '5',
  shift: 'morning',
  room: 'Sala 1',
  capacity: 30,
  isActive: true,
  studentCount: 3,
}

function student(id: string, fullName: string, enrollmentNumber: string): Student {
  return {
    id,
    fullName,
    enrollmentNumber,
    birthDate: '2016-03-14',
    archivedAt: null,
    currentClassId: schoolClass.id,
    currentEnrollmentId: `enrollment-${id}`,
  }
}

type Db = {
  users: Record<string, Me>
  years: SchoolYear[]
  subjects: Subject[]
  classes: SchoolClass[]
  assignments: SubjectTeacher[]
  students: Student[]
  marks: Record<string, AttendanceStatus>
  notes: string | null
  rollCallId: string | null
  savedRollCalls: RollCallUpsertInput[]
  createdStudents: unknown[]
  sheetEditable: boolean
}

function initialDb(): Db {
  return {
    users: { [admin.email]: admin, [teacher.email]: teacher },
    years: [year],
    subjects: [subject],
    classes: [schoolClass],
    assignments: [
      {
        subjectId: subject.id,
        subjectName: subject.name,
        subjectCode: subject.code,
        teacherId: teacher.id,
        teacherName: teacher.fullName,
      },
    ],
    students: [
      student('student-bruno', 'Bruno Martins', '202600002'),
      student('student-alice', 'Alice Souza', '202600001'),
      student('student-carla', 'Carla Ferreira', '202600003'),
    ],
    marks: {},
    notes: null,
    rollCallId: null,
    savedRollCalls: [],
    createdStudents: [],
    sheetEditable: true,
  }
}

export let db: Db = initialDb()

export function resetDb() {
  db = initialDb()
}

export function sheetStudents(): SheetStudent[] {
  return [...db.students]
    .sort((a, b) => a.fullName.localeCompare(b.fullName))
    .map((s) => ({
      studentId: s.id,
      fullName: s.fullName,
      enrollmentNumber: s.enrollmentNumber,
      status: db.marks[s.id] ?? null,
    }))
}
