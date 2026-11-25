import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import type {
  AttendanceSummary,
  ClassReportRow,
  DashboardToday,
  Me,
  RollCallSheet,
  RollCallUpsertInput,
  StudentCreateInput,
  StudentDetail,
  StudentReportRow,
} from '@/shared/api/types'
import { db, sheetStudents, TODAY } from './db'

const API = '/api/v1'
const ACCESS_PREFIX = 'token-for:'

function page<T>(items: T[]) {
  return { items, total: items.length, page: 1, pageSize: 20 }
}

function problem(
  status: number,
  code: string,
  fieldErrors: { field: string; code: string }[] = [],
) {
  return HttpResponse.json(
    { type: 'about:blank', title: code, status, code, detail: code, fieldErrors },
    { status, headers: { 'Content-Type': 'application/problem+json' } },
  )
}

function currentUser(request: Request): Me | null {
  const header = request.headers.get('Authorization') ?? ''
  const email = header.replace(`Bearer ${ACCESS_PREFIX}`, '')
  return db.users[email] ?? null
}

function authed<T extends unknown[]>(
  handler: (user: Me, request: Request, ...rest: T) => Response | Promise<Response>,
) {
  return async ({ request }: { request: Request }, ...rest: T) => {
    const user = currentUser(request)
    if (!user) return problem(401, 'not_authenticated')
    return handler(user, request, ...rest)
  }
}

export const sessionCookie = { email: null as string | null }

const summary: AttendanceSummary = {
  dateFrom: '2026-11-01',
  dateTo: '2026-11-30',
  schoolDays: 20,
  lessons: 9,
  students: 3,
  present: 11,
  absent: 3,
  attendanceRate: 78.6,
  atRiskStudents: 1,
  minAttendanceRate: 75,
}

const reportRows: StudentReportRow[] = [
  {
    studentId: 'student-alice',
    fullName: 'Alice Souza',
    enrollmentNumber: '202600001',
    classId: 'class-5a',
    className: '5º Ano A',
    present: 5,
    absent: 0,
    total: 5,
    attendanceRate: 100,
    atRisk: false,
  },
  {
    studentId: 'student-bruno',
    fullName: 'Bruno Martins',
    enrollmentNumber: '202600002',
    classId: 'class-5a',
    className: '5º Ano A',
    present: 3,
    absent: 2,
    total: 5,
    attendanceRate: 60,
    atRisk: true,
  },
]

const byClass: ClassReportRow[] = [
  {
    classId: 'class-5a',
    className: '5º Ano A',
    lessons: 5,
    students: 2,
    present: 8,
    absent: 2,
    attendanceRate: 80,
    atRiskStudents: 1,
  },
]

export const handlers = [
  http.post(`${API}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string }
    const user = db.users[body.email.toLowerCase()]
    const passwords: Record<string, string> = {
      'diretoria@example.com': 'senha-da-diretoria',
      'professora@example.com': 'senha-da-professora',
    }
    if (!user || passwords[user.email] !== body.password) return problem(401, 'invalid_credentials')
    sessionCookie.email = user.email
    return HttpResponse.json({
      accessToken: `${ACCESS_PREFIX}${user.email}`,
      tokenType: 'bearer',
      expiresIn: 900,
      user,
    })
  }),
  http.post(`${API}/auth/refresh`, () => {
    if (!sessionCookie.email) return problem(401, 'invalid_refresh_token')
    return HttpResponse.json({
      accessToken: `${ACCESS_PREFIX}${sessionCookie.email}`,
      tokenType: 'bearer',
      expiresIn: 900,
      user: db.users[sessionCookie.email],
    })
  }),
  http.post(`${API}/auth/logout`, () => {
    sessionCookie.email = null
    return new HttpResponse(null, { status: 204 })
  }),
  http.get(
    `${API}/auth/me`,
    authed((user) => HttpResponse.json(user)),
  ),

  http.get(
    `${API}/school-years`,
    authed(() => HttpResponse.json(page(db.years))),
  ),
  http.get(
    `${API}/school-years/:id/terms`,
    authed(() => HttpResponse.json({ items: [], total: 0 })),
  ),
  http.get(
    `${API}/subjects`,
    authed(() => HttpResponse.json(page(db.subjects))),
  ),
  http.get(
    `${API}/classes`,
    authed(() => HttpResponse.json(page(db.classes))),
  ),
  http.get(
    `${API}/classes/:id/subject-teachers`,
    authed(() => HttpResponse.json({ items: db.assignments, total: db.assignments.length })),
  ),

  http.get(
    `${API}/dashboard/today`,
    authed(() =>
      HttpResponse.json<DashboardToday>({
        date: TODAY,
        schoolYearId: 'year-2026',
        schoolYearName: '2026',
        isSchoolDay: true,
        totalClasses: 1,
        totalStudents: 3,
        rollCallsExpected: 1,
        rollCallsDone: 0,
        presenceRateToday: null,
        presenceRateLast30Days: 82.5,
        pendingRollCalls: [
          {
            classId: 'class-5a',
            className: '5º Ano A',
            subjectId: 'subject-math',
            subjectName: 'Matemática',
            teacherId: 'user-teacher',
            teacherName: 'Ana Professora',
          },
        ],
        lowAttendanceStudents: [
          {
            studentId: 'student-bruno',
            fullName: 'Bruno Martins',
            classId: 'class-5a',
            className: '5º Ano A',
            attendanceRate: 60,
          },
        ],
      }),
    ),
  ),

  http.get(
    `${API}/roll-calls/sheet`,
    authed((_user, request) => {
      const url = new URL(request.url)
      return HttpResponse.json<RollCallSheet>({
        classId: url.searchParams.get('classId') ?? '',
        subjectId: url.searchParams.get('subjectId') ?? '',
        lessonDate: url.searchParams.get('date') ?? TODAY,
        rollCallId: db.rollCallId,
        notes: db.notes,
        isSchoolDay: true,
        editable: db.sheetEditable,
        students: sheetStudents(),
      })
    }),
  ),
  http.put(
    `${API}/roll-calls`,
    authed(async (user, request) => {
      const body = (await request.json()) as RollCallUpsertInput
      db.savedRollCalls.push(body)
      db.rollCallId = 'roll-call-1'
      db.notes = body.notes ?? null
      for (const mark of body.attendances) db.marks[mark.studentId] = mark.status
      const present = body.attendances.filter((a) => a.status === 'present').length
      return HttpResponse.json({
        id: db.rollCallId,
        classId: body.classId,
        subjectId: body.subjectId,
        lessonDate: body.lessonDate,
        notes: body.notes,
        takenById: user.id,
        updatedById: user.id,
        createdAt: `${TODAY}T10:00:00Z`,
        updatedAt: `${TODAY}T10:00:00Z`,
        presentCount: present,
        absentCount: body.attendances.length - present,
        attendances: body.attendances,
      })
    }),
  ),

  http.get(
    `${API}/students`,
    authed(() => HttpResponse.json(page(db.students))),
  ),
  http.post(
    `${API}/students`,
    authed(async (_user, request) => {
      const body = (await request.json()) as StudentCreateInput
      db.createdStudents.push(body)
      return HttpResponse.json<StudentDetail>(
        {
          id: 'student-new',
          fullName: body.fullName,
          enrollmentNumber: '202600099',
          birthDate: body.birthDate,
          archivedAt: null,
          currentClassId: body.classId ?? null,
          currentEnrollmentId: body.classId ? 'enrollment-new' : null,
          guardians: [],
        },
        { status: 201 },
      )
    }),
  ),

  http.get(
    `${API}/reports/attendance/summary`,
    authed(() => HttpResponse.json(summary)),
  ),
  http.get(
    `${API}/reports/attendance/students`,
    authed(() => HttpResponse.json({ items: reportRows, total: reportRows.length })),
  ),
  http.get(
    `${API}/reports/attendance/by-class`,
    authed(() => HttpResponse.json({ items: byClass, total: byClass.length })),
  ),
  http.get(
    `${API}/reports/attendance/export`,
    authed(
      () =>
        new HttpResponse('Matrícula;Aluno\r\n', {
          headers: { 'Content-Type': 'text/csv; charset=utf-8' },
        }),
    ),
  ),
]

export const server = setupServer(...handlers)

export { problem }
