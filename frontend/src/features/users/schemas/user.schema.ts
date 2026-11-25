import { z } from 'zod'

export const UserSchema = z.object({
  fullName: z
    .string()
    .trim()
    .min(3, 'Informe o nome completo.')
    .max(200, 'Use no máximo 200 caracteres.'),
  email: z.string().trim().min(1, 'Informe o e-mail.').email('Informe um e-mail válido.'),
  role: z.enum(['admin', 'teacher'], { message: 'Escolha o perfil.' }),
})
export type UserForm = z.infer<typeof UserSchema>
