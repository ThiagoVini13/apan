import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useLocation } from 'react-router-dom'
import { applyApiErrors } from '@/shared/lib/form'
import { Button } from '@/shared/ui/Button'
import { Field, Input } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { CheckIcon } from '@/shared/ui/icons'
import { useResetPassword } from '../api/auth.queries'
import { AuthLayout } from '../components/AuthLayout'
import { NewPasswordSchema, type NewPasswordForm } from '../schemas/auth.schema'

function tokenFromHash(hash: string) {
  return new URLSearchParams(hash.replace(/^#/, '')).get('token') ?? ''
}

export default function ResetPasswordPage() {
  const location = useLocation()
  const [token] = useState(() => tokenFromHash(location.hash))
  const reset = useResetPassword()
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<NewPasswordForm>({ resolver: zodResolver(NewPasswordSchema), mode: 'onTouched' })

  const onSubmit = handleSubmit(({ newPassword }) => {
    setSummary(null)
    reset.mutate(
      { token, newPassword },
      { onError: (error) => setSummary(applyApiErrors(error, setError, ['newPassword'])) },
    )
  })

  if (!token) {
    return (
      <AuthLayout
        title="Link inválido"
        description="O link está incompleto. Peça um novo para continuar."
      >
        <Link to="/forgot-password" className="font-medium text-primary-text underline">
          Pedir um novo link
        </Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      title="Criar nova senha"
      description="Use pelo menos 10 caracteres. Uma frase fácil de lembrar funciona bem."
    >
      {reset.isSuccess ? (
        <div role="status" className="flex flex-col gap-4">
          <p className="flex items-start gap-2 rounded-lg border border-success bg-success-bg p-3 text-sm text-fg">
            <CheckIcon className="mt-0.5 size-4 text-success" />
            Senha definida. Agora é só entrar com o seu e-mail e a nova senha.
          </p>
          <Link to="/login" className="text-center font-medium text-primary-text underline">
            Ir para o login
          </Link>
        </div>
      ) : (
        <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
          <FormErrorSummary message={summary} />
          <Field label="Nova senha" error={errors.newPassword?.message} required>
            {(props) => (
              <Input
                {...props}
                type="password"
                autoComplete="new-password"
                {...register('newPassword')}
              />
            )}
          </Field>
          <Field label="Repita a nova senha" error={errors.confirmPassword?.message} required>
            {(props) => (
              <Input
                {...props}
                type="password"
                autoComplete="new-password"
                {...register('confirmPassword')}
              />
            )}
          </Field>
          <Button type="submit" isPending={reset.isPending} pendingLabel="Salvando…">
            Salvar senha
          </Button>
        </form>
      )}
    </AuthLayout>
  )
}
