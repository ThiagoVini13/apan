import { z } from 'zod'
import type { Relationship } from '@/shared/api/types'
import { ADULT_AGE, MIN_ENROLLMENT_AGE } from '@/shared/lib/constants'
import { calculateAge, isIsoDate, todayIso } from '@/shared/lib/date'
import { isValidPhone } from '@/shared/lib/phone'

const RELATIONSHIPS = [
  'mother',
  'father',
  'grandparent',
  'sibling',
  'uncle_aunt',
  'legal_guardian',
  'other',
] as const satisfies readonly Relationship[]

const fullName = z
  .string()
  .trim()
  .min(3, 'Informe o nome completo.')
  .max(200, 'Use no máximo 200 caracteres.')

const birthDate = z
  .string()
  .min(1, 'Informe a data de nascimento.')
  .refine(isIsoDate, 'Informe uma data válida.')
  .refine((value) => value <= todayIso(), 'A data de nascimento não pode ser futura.')
  .refine(
    (value) => !isIsoDate(value) || calculateAge(value) >= MIN_ENROLLMENT_AGE,
    `O aluno precisa ter pelo menos ${MIN_ENROLLMENT_AGE} anos.`,
  )

export const GuardianSchema = z.object({
  fullName,
  phone: z.string().refine(isValidPhone, 'Informe DDD e número, por exemplo (92) 99123-4567.'),
  relationship: z.enum(RELATIONSHIPS, { message: 'Escolha o parentesco.' }),
})
export type GuardianForm = z.infer<typeof GuardianSchema>

export function isMinor(birth: string) {
  return isIsoDate(birth) && calculateAge(birth) < ADULT_AGE
}

export function makeStudentCreateSchema({ requireClass }: { requireClass: boolean }) {
  return z
    .object({
      fullName,
      birthDate,
      classId: z.string(),
      guardianName: z.string().trim(),
      guardianPhone: z.string(),
      guardianRelationship: z.union([z.enum(RELATIONSHIPS), z.literal('')]),
    })
    .superRefine((data, ctx) => {
      if (requireClass && !data.classId) {
        ctx.addIssue({ code: 'custom', path: ['classId'], message: 'Escolha a turma do aluno.' })
      }
      const hasGuardian = !!(data.guardianName || data.guardianPhone || data.guardianRelationship)
      if (!isMinor(data.birthDate) && !hasGuardian) return
      if (data.guardianName.length < 3) {
        ctx.addIssue({
          code: 'custom',
          path: ['guardianName'],
          message: 'Alunos menores de 18 anos precisam de um responsável. Informe o nome completo.',
        })
      }
      if (!isValidPhone(data.guardianPhone)) {
        ctx.addIssue({
          code: 'custom',
          path: ['guardianPhone'],
          message: 'Informe DDD e número, por exemplo (92) 99123-4567.',
        })
      }
      if (!data.guardianRelationship) {
        ctx.addIssue({
          code: 'custom',
          path: ['guardianRelationship'],
          message: 'Escolha o parentesco.',
        })
      }
    })
}
export type StudentCreateForm = z.infer<ReturnType<typeof makeStudentCreateSchema>>

export const StudentUpdateSchema = z.object({ fullName, birthDate })
export type StudentUpdateForm = z.infer<typeof StudentUpdateSchema>
