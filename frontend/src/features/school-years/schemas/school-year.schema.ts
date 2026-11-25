import { z } from 'zod'
import { isIsoDate } from '@/shared/lib/date'

const isoDate = z.string().refine(isIsoDate, 'Informe uma data válida.')

export const SchoolYearSchema = z
  .object({
    name: z
      .string()
      .trim()
      .min(1, 'Informe o nome, por exemplo 2026.')
      .max(50, 'Use no máximo 50 caracteres.'),
    startsOn: isoDate,
    endsOn: isoDate,
    isCurrent: z.boolean(),
  })
  .refine((data) => data.endsOn > data.startsOn, {
    path: ['endsOn'],
    message: 'O término deve ser depois do início.',
  })
export type SchoolYearForm = z.infer<typeof SchoolYearSchema>

export const TermSchema = z
  .object({
    name: z
      .string()
      .trim()
      .min(1, 'Informe o nome, por exemplo 1º bimestre.')
      .max(50, 'Use no máximo 50 caracteres.'),
    startsOn: isoDate,
    endsOn: isoDate,
  })
  .refine((data) => data.endsOn >= data.startsOn, {
    path: ['endsOn'],
    message: 'O término deve ser igual ou depois do início.',
  })
export type TermForm = z.infer<typeof TermSchema>

export const CalendarDaySchema = z.object({
  day: isoDate,
  kind: z.enum(['holiday', 'recess', 'non_school_day', 'extra_school_day'], {
    message: 'Escolha o tipo.',
  }),
  description: z.string().trim().max(200, 'Use no máximo 200 caracteres.'),
})
export type CalendarDayForm = z.infer<typeof CalendarDaySchema>
