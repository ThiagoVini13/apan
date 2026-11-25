import { z } from 'zod'

export const ClassSchema = z.object({
  schoolYearId: z.string().min(1, 'Escolha o ano letivo.'),
  name: z
    .string()
    .trim()
    .min(1, 'Informe o nome da turma, por exemplo 5º Ano A.')
    .max(50, 'Use no máximo 50 caracteres.'),
  grade: z
    .string()
    .trim()
    .min(1, 'Informe a série ou etapa.')
    .max(20, 'Use no máximo 20 caracteres.'),
  shift: z.enum(['morning', 'afternoon', 'evening'], { message: 'Escolha o turno.' }),
  room: z.string().trim().max(50, 'Use no máximo 50 caracteres.'),
  capacity: z
    .string()
    .trim()
    .refine(
      (value) =>
        value === '' || (/^\d+$/.test(value) && Number(value) >= 1 && Number(value) <= 500),
      {
        message: 'Informe um número entre 1 e 500, ou deixe em branco.',
      },
    ),
})
export type ClassForm = z.infer<typeof ClassSchema>
