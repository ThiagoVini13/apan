import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { errorMessage } from '@/shared/lib/errors'
import { useSession } from '@/shared/session/session'
import { Button } from '@/shared/ui/Button'
import { Field, Input } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { useLogin } from '../api/auth.queries'
import { AuthLayout } from '../components/AuthLayout'
import { LoginSchema, type LoginForm } from '../schemas/auth.schema'

function safeNext(next: string | null) {
  return next && next.startsWith('/') && !next.startsWith('//') ? next : '/'
}

export default function LoginPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { data: user } = useSession()
  const login = useLogin()
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(LoginSchema), mode: 'onTouched' })

  const next = safeNext(searchParams.get('next'))
  if (user) return <Navigate to={user.mustChangePassword ? '/change-password' : next} replace />

  const onSubmit = handleSubmit((data) => {
    setSummary(null)
    login.mutate(data, {
      onSuccess: (tokens) =>
        navigate(tokens.user.mustChangePassword ? '/change-password' : next, { replace: true }),
      onError: (error) => setSummary(errorMessage(error)),
    })
  })

  return (
    <AuthLayout title="Entrar" description="Use o e-mail e a senha da sua conta.">
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        <FormErrorSummary message={summary} />
        <Field label="E-mail" error={errors.email?.message} required>
          {(props) => (
            <Input {...props} type="email" autoComplete="username" {...register('email')} />
          )}
        </Field>
        <Field label="Senha" error={errors.password?.message} required>
          {(props) => (
            <Input
              {...props}
              type="password"
              autoComplete="current-password"
              {...register('password')}
            />
          )}
        </Field>
        <Button type="submit" isPending={login.isPending} pendingLabel="Entrando…">
          Entrar
        </Button>
        <Link
          to="/forgot-password"
          className="text-center text-sm font-medium text-primary-text underline"
        >
          Esqueci minha senha
        </Link>
      </form>
    </AuthLayout>
  )
}
