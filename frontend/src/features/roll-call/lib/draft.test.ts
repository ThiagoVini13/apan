import { describe, expect, it } from 'vitest'
import type { RollCallSheet } from '@/shared/api/types'
import { countMarks, draftReducer, firstPending, initialDraft } from './draft'

const sheet: RollCallSheet = {
  classId: 'c',
  subjectId: 's',
  lessonDate: '2026-11-24',
  rollCallId: null,
  notes: null,
  isSchoolDay: true,
  editable: true,
  students: [
    { studentId: 'a', fullName: 'A', enrollmentNumber: '1', status: 'present' },
    { studentId: 'b', fullName: 'B', enrollmentNumber: '2', status: null },
    { studentId: 'c', fullName: 'C', enrollmentNumber: '3', status: null },
  ],
}

describe('roll call draft', () => {
  it('starts from the saved marks and is not dirty', () => {
    const draft = initialDraft(sheet)

    expect(draft.isDirty).toBe(false)
    expect(countMarks(draft.marks)).toEqual({ present: 1, absent: 0, pending: 2 })
    expect(firstPending(['a', 'b', 'c'], draft.marks)).toBe('b')
  })

  it('marks students, marks everyone present and keeps notes', () => {
    let draft = draftReducer(initialDraft(sheet), {
      type: 'mark',
      studentId: 'b',
      status: 'absent',
    })
    draft = draftReducer(draft, { type: 'notes', value: 'Frações' })

    expect(draft.isDirty).toBe(true)
    expect(countMarks(draft.marks)).toEqual({ present: 1, absent: 1, pending: 1 })

    draft = draftReducer(draft, { type: 'markAllPresent' })
    expect(countMarks(draft.marks)).toEqual({ present: 3, absent: 0, pending: 0 })
    expect(draft.notes).toBe('Frações')
  })
})
