import { z } from 'zod'
import { MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH } from '@/shared/lib/constants'

const email = z.string().trim().min(1, 'Informe o e-mail.').email('Informe um e-mail válido.')

const newPassword = z
  .string()
  .min(MIN_PASSWORD_LENGTH, `Use pelo menos ${MIN_PASSWORD_LENGTH} caracteres.`)
  .max(MAX_PASSWORD_LENGTH, `Use no máximo ${MAX_PASSWORD_LENGTH} caracteres.`)

export const LoginSchema = z.object({
  email,
  password: z.string().min(1, 'Informe a senha.'),
})
export type LoginForm = z.infer<typeof LoginSchema>

export const ForgotPasswordSchema = z.object({ email })
export type ForgotPasswordForm = z.infer<typeof ForgotPasswordSchema>

export const NewPasswordSchema = z
  .object({
    newPassword,
    confirmPassword: z.string().min(1, 'Repita a nova senha.'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'As senhas não coincidem.',
  })
export type NewPasswordForm = z.infer<typeof NewPasswordSchema>

export const ChangePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Informe a senha atual.'),
    newPassword,
    confirmPassword: z.string().min(1, 'Repita a nova senha.'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'As senhas não coincidem.',
  })
export type ChangePasswordForm = z.infer<typeof ChangePasswordSchema>
