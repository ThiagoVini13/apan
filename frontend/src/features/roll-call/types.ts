import type { AttendanceStatus } from '@/shared/api/types'

export type SheetParams = { classId: string; subjectId: string; date: string }

export type Marks = Record<string, AttendanceStatus | null>
