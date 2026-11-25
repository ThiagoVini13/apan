import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { applyApiErrors } from '@/shared/lib/form'
import { useCurrentUser } from '@/shared/session/session'
import { Button } from '@/shared/ui/Button'
import { Field, Input } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { Card, PageHeader } from '@/shared/ui/Layout'
import { notify } from '@/shared/ui/toast.store'
import { useChangePassword } from '../api/auth.queries'
import { ChangePasswordSchema, type ChangePasswordForm } from '../schemas/auth.schema'

export default function ChangePasswordPage() {
  useDocumentTitle('Alterar senha')
  const user = useCurrentUser()
  const navigate = useNavigate()
  const change = useChangePassword()
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<ChangePasswordForm>({
    resolver: zodResolver(ChangePasswordSchema),
    mode: 'onTouched',
  })

  const onSubmit = handleSubmit(({ currentPassword, newPassword }) => {
    setSummary(null)
    change.mutate(
      { currentPassword, newPassword },
      {
        onSuccess: () => {
          reset()
          notify.success('Senha alterada. As outras sessões abertas foram encerradas.')
          if (user.mustChangePassword) navigate('/', { replace: true })
        },
        onError: (error) =>
          setSummary(applyApiErrors(error, setError, ['currentPassword', 'newPassword'])),
      },
    )
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Alterar senha"
        description={
          user.mustChangePassword
            ? 'Antes de continuar, defina uma nova senha para a sua conta.'
            : 'Ao trocar a senha, as sessões abertas em outros aparelhos são encerradas.'
        }
      />
      <Card className="max-w-lg">
        <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
          <FormErrorSummary message={summary} />
          <Field label="Senha atual" error={errors.currentPassword?.message} required>
            {(props) => (
              <Input
                {...props}
                type="password"
                autoComplete="current-password"
                {...register('currentPassword')}
              />
            )}
          </Field>
          <Field
            label="Nova senha"
            hint="Pelo menos 10 caracteres. Evite senhas comuns e o seu e-mail."
            error={errors.newPassword?.message}
            required
          >
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
          <Button
            type="submit"
            isPending={change.isPending}
            pendingLabel="Salvando…"
            className="self-start"
          >
            Salvar nova senha
          </Button>
        </form>
      </Card>
    </div>
  )
}
