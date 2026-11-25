import { z } from 'zod'

export const SubjectSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, 'Informe o nome da disciplina.')
    .max(100, 'Use no máximo 100 caracteres.'),
  code: z
    .string()
    .trim()
    .min(1, 'Informe um código curto, por exemplo MAT.')
    .max(20, 'Use no máximo 20 caracteres.')
    .regex(/^[A-Za-z0-9_-]+$/, 'Use apenas letras, números, hífen ou sublinhado.'),
})
export type SubjectForm = z.infer<typeof SubjectSchema>
