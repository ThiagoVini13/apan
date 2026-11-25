import { describe, expect, it } from 'vitest'
import { makeStudentCreateSchema } from './student.schema'

const base = {
  fullName: 'Alice Souza',
  birthDate: '2016-03-14',
  classId: 'class-5a',
  guardianName: 'Maria Souza',
  guardianPhone: '(92) 99123-4567',
  guardianRelationship: 'mother' as const,
}

function errorPaths(input: Record<string, unknown>, requireClass = false) {
  const result = makeStudentCreateSchema({ requireClass }).safeParse(input)
  return result.success ? [] : result.error.issues.map((issue) => issue.path.join('.'))
}

describe('student create schema', () => {
  it('accepts a minor with a guardian', () => {
    expect(errorPaths(base)).toEqual([])
  })

  it('requires a guardian for minors', () => {
    const paths = errorPaths({
      ...base,
      guardianName: '',
      guardianPhone: '',
      guardianRelationship: '',
    })

    expect(paths).toEqual(['guardianName', 'guardianPhone', 'guardianRelationship'])
  })

  it('does not require a guardian for adults', () => {
    const adult = {
      ...base,
      birthDate: '2000-05-10',
      guardianName: '',
      guardianPhone: '',
      guardianRelationship: '',
    }

    expect(errorPaths(adult)).toEqual([])
  })

  it('rejects children younger than 3 and future dates', () => {
    const nextYear = `${new Date().getFullYear() + 1}-01-01`

    expect(errorPaths({ ...base, birthDate: nextYear })).toContain('birthDate')
    expect(errorPaths({ ...base, birthDate: `${new Date().getFullYear() - 1}-01-01` })).toContain(
      'birthDate',
    )
  })

  it('requires the class when registering as a teacher', () => {
    expect(errorPaths({ ...base, classId: '' }, true)).toEqual(['classId'])
    expect(errorPaths({ ...base, classId: '' }, false)).toEqual([])
  })

  it('validates the guardian phone', () => {
    expect(errorPaths({ ...base, guardianPhone: '1234' })).toEqual(['guardianPhone'])
  })
})
