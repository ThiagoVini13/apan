import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import type { User } from '@/shared/api/types'
import { applyApiErrors } from '@/shared/lib/form'
import { optionsFrom, roleLabels } from '@/shared/lib/labels'
import { Button } from '@/shared/ui/Button'
import { Dialog } from '@/shared/ui/Dialog'
import { Field, Input, RequiredFieldsNote, Select } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { notify } from '@/shared/ui/toast.store'
import { useInviteUser, useUpdateUser } from '../api/users.queries'
import { UserSchema, type UserForm } from '../schemas/user.schema'

type UserFormDialogProps = { user: User | null; onClose: () => void }

const roleOptions = optionsFrom(roleLabels)

export function UserFormDialog({ user, onClose }: UserFormDialogProps) {
  const invite = useInviteUser()
  const update = useUpdateUser()
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<UserForm>({
    resolver: zodResolver(UserSchema),
    mode: 'onTouched',
    defaultValues: user
      ? { fullName: user.fullName, email: user.email, role: user.role }
      : { fullName: '', email: '', role: 'teacher' },
  })

  const onSubmit = handleSubmit((data) => {
    setSummary(null)
    const onError = (error: unknown) =>
      setSummary(applyApiErrors(error, setError, ['fullName', 'email', 'role']))
    if (user) {
      update.mutate(
        { id: user.id, data },
        {
          onSuccess: () => {
            notify.success('Usuário atualizado.')
            onClose()
          },
          onError,
        },
      )
    } else {
      invite.mutate(data, {
        onSuccess: (created) => {
          notify.success(`Convite enviado para ${created.email}.`)
          onClose()
        },
        onError,
      })
    }
  })

  return (
    <Dialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={user ? 'Editar usuário' : 'Convidar usuário'}
      description={
        user
          ? undefined
          : 'A pessoa recebe um e-mail com um link para definir a própria senha (válido por 72 horas).'
      }
    >
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        <RequiredFieldsNote />
        <FormErrorSummary message={summary} />
        <Field label="Nome completo" error={errors.fullName?.message} required>
          {(props) => <Input {...props} autoComplete="name" {...register('fullName')} />}
        </Field>
        <Field label="E-mail" error={errors.email?.message} required>
          {(props) => <Input {...props} type="email" autoComplete="email" {...register('email')} />}
        </Field>
        <Field label="Perfil" error={errors.role?.message} required>
          {(props) => (
            <Select {...props} {...register('role')}>
              {roleOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isPending={invite.isPending || update.isPending}>
            {user ? 'Salvar' : 'Enviar convite'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
