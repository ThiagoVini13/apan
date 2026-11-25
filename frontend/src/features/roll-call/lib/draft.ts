import type { AttendanceStatus, RollCallSheet } from '@/shared/api/types'
import type { Marks } from '../types'

export type Draft = { marks: Marks; notes: string; isDirty: boolean }

export type DraftAction =
  | { type: 'mark'; studentId: string; status: AttendanceStatus }
  | { type: 'markAllPresent' }
  | { type: 'notes'; value: string }

export function initialDraft(sheet: RollCallSheet): Draft {
  return {
    marks: Object.fromEntries(sheet.students.map((s) => [s.studentId, s.status ?? null])),
    notes: sheet.notes ?? '',
    isDirty: false,
  }
}

export function draftReducer(state: Draft, action: DraftAction): Draft {
  switch (action.type) {
    case 'mark':
      return {
        ...state,
        isDirty: true,
        marks: { ...state.marks, [action.studentId]: action.status },
      }
    case 'markAllPresent':
      return {
        ...state,
        isDirty: true,
        marks: Object.fromEntries(Object.keys(state.marks).map((id) => [id, 'present'])),
      }
    case 'notes':
      return { ...state, isDirty: true, notes: action.value }
  }
}

export function countMarks(marks: Marks) {
  const values = Object.values(marks)
  return {
    present: values.filter((status) => status === 'present').length,
    absent: values.filter((status) => status === 'absent').length,
    pending: values.filter((status) => status === null).length,
  }
}

export function firstPending(order: string[], marks: Marks): string | undefined {
  return order.find((id) => marks[id] === null)
}
