import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { errorMessage } from '@/shared/lib/errors'
import { Button } from '@/shared/ui/Button'
import { Field, Input } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { CheckIcon } from '@/shared/ui/icons'
import { useForgotPassword } from '../api/auth.queries'
import { AuthLayout } from '../components/AuthLayout'
import { ForgotPasswordSchema, type ForgotPasswordForm } from '../schemas/auth.schema'

export default function ForgotPasswordPage() {
  const forgot = useForgotPassword()
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordForm>({
    resolver: zodResolver(ForgotPasswordSchema),
    mode: 'onTouched',
  })

  const onSubmit = handleSubmit(({ email }) => {
    setSummary(null)
    forgot.mutate(email, { onError: (error) => setSummary(errorMessage(error)) })
  })

  return (
    <AuthLayout
      title="Esqueci minha senha"
      description="Informe o seu e-mail. Se ele estiver cadastrado, você receberá um link para criar uma nova senha."
    >
      {forgot.isSuccess ? (
        <div role="status" className="flex flex-col gap-4">
          <p className="flex items-start gap-2 rounded-lg border border-success bg-success-bg p-3 text-sm text-fg">
            <CheckIcon className="mt-0.5 size-4 text-success" />
            Pronto. Se o e-mail estiver cadastrado, o link chega em alguns minutos e vale por 30
            minutos.
          </p>
          <Link to="/login" className="text-center text-sm font-medium text-primary-text underline">
            Voltar para o login
          </Link>
        </div>
      ) : (
        <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
          <FormErrorSummary message={summary} />
          <Field label="E-mail" error={errors.email?.message} required>
            {(props) => (
              <Input {...props} type="email" autoComplete="email" {...register('email')} />
            )}
          </Field>
          <Button type="submit" isPending={forgot.isPending} pendingLabel="Enviando…">
            Enviar link
          </Button>
          <Link to="/login" className="text-center text-sm font-medium text-primary-text underline">
            Voltar para o login
          </Link>
        </form>
      )}
    </AuthLayout>
  )
}
