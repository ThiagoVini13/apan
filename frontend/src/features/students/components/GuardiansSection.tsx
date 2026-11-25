import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import type { Guardian } from '@/shared/api/types'
import { applyApiErrors } from '@/shared/lib/form'
import { formatPhone } from '@/shared/lib/format'
import { optionsFrom, relationshipLabels } from '@/shared/lib/labels'
import { phoneDigits } from '@/shared/lib/phone'
import { Badge } from '@/shared/ui/Badge'
import { Button } from '@/shared/ui/Button'
import { ConfirmDialog } from '@/shared/ui/Dialog'
import { Field, Input, Select } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { PlusIcon, StarIcon, TrashIcon } from '@/shared/ui/icons'
import { PhoneInput } from '@/shared/ui/PhoneInput'
import { notify } from '@/shared/ui/toast.store'
import { useAddGuardian, useDeleteGuardian, useUpdateGuardian } from '../api/students.queries'
import { GuardianSchema, type GuardianForm } from '../schemas/student.schema'

const relationshipOptions = optionsFrom(relationshipLabels)

type GuardiansSectionProps = { studentId: string; guardians: Guardian[]; disabled: boolean }

export function GuardiansSection({ studentId, guardians, disabled }: GuardiansSectionProps) {
  const [isAdding, setIsAdding] = useState(false)
  const [toRemove, setToRemove] = useState<Guardian | null>(null)
  const update = useUpdateGuardian(studentId)
  const remove = useDeleteGuardian(studentId)

  return (
    <section aria-labelledby="guardians-heading" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 id="guardians-heading" className="font-semibold text-fg">
          Responsáveis
        </h3>
        {!disabled && !isAdding && (
          <Button variant="secondary" onClick={() => setIsAdding(true)}>
            <PlusIcon className="size-4" />
            Adicionar responsável
          </Button>
        )}
      </div>

      {guardians.length === 0 && (
        <p className="text-sm text-fg-muted">Nenhum responsável cadastrado.</p>
      )}

      <ul className="flex flex-col gap-2">
        {guardians.map((guardian) => (
          <li
            key={guardian.id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line p-3"
          >
            <div>
              <p className="flex flex-wrap items-center gap-2 font-medium text-fg">
                {guardian.fullName}
                {guardian.isPrimary && (
                  <Badge tone="info" icon={<StarIcon className="size-3.5" />}>
                    Principal
                  </Badge>
                )}
              </p>
              <p className="text-sm text-fg-muted">
                {relationshipLabels[guardian.relationship]} · {formatPhone(guardian.phone)}
              </p>
            </div>
            {!disabled && (
              <div className="flex flex-wrap gap-2">
                {!guardian.isPrimary && (
                  <Button
                    variant="ghost"
                    aria-label={`Tornar ${guardian.fullName} responsável principal`}
                    onClick={() =>
                      update.mutate(
                        { guardianId: guardian.id, data: { isPrimary: true } },
                        { onSuccess: () => notify.success('Responsável principal atualizado.') },
                      )
                    }
                  >
                    <StarIcon className="size-4" />
                    Tornar principal
                  </Button>
                )}
                <Button
                  variant="danger"
                  aria-label={`Remover ${guardian.fullName}`}
                  onClick={() => setToRemove(guardian)}
                >
                  <TrashIcon className="size-4" />
                  Remover
                </Button>
              </div>
            )}
          </li>
        ))}
      </ul>

      {isAdding && <GuardianAddForm studentId={studentId} onDone={() => setIsAdding(false)} />}

      <ConfirmDialog
        open={toRemove !== null}
        onOpenChange={(open) => !open && setToRemove(null)}
        title="Remover responsável?"
        description={toRemove ? `${toRemove.fullName} deixará de constar como responsável.` : ''}
        confirmLabel="Remover"
        tone="danger"
        isPending={remove.isPending}
        onConfirm={() =>
          toRemove &&
          remove.mutate(toRemove.id, {
            onSuccess: () => {
              notify.success('Responsável removido.')
              setToRemove(null)
            },
            onSettled: () => setToRemove(null),
          })
        }
      />
    </section>
  )
}

function GuardianAddForm({ studentId, onDone }: { studentId: string; onDone: () => void }) {
  const add = useAddGuardian(studentId)
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<GuardianForm>({
    resolver: zodResolver(GuardianSchema),
    mode: 'onTouched',
    defaultValues: { fullName: '', phone: '', relationship: undefined },
  })

  const onSubmit = handleSubmit((data) => {
    setSummary(null)
    add.mutate(
      { ...data, phone: phoneDigits(data.phone), isPrimary: false },
      {
        onSuccess: () => {
          notify.success('Responsável adicionado.')
          onDone()
        },
        onError: (error) => setSummary(applyApiErrors(error, setError, ['fullName', 'phone'])),
      },
    )
  })

  return (
    <form
      onSubmit={onSubmit}
      noValidate
      className="grid gap-4 rounded-lg border border-line p-4 sm:grid-cols-2"
    >
      <FormErrorSummary message={summary} />
      <Field
        label="Nome do responsável"
        error={errors.fullName?.message}
        required
        className="sm:col-span-2"
      >
        {(props) => <Input {...props} autoComplete="off" {...register('fullName')} />}
      </Field>
      <Field label="Telefone" error={errors.phone?.message} required>
        {(props) => (
          <Controller
            control={control}
            name="phone"
            render={({ field }) => (
              <PhoneInput
                {...props}
                value={field.value}
                onChange={field.onChange}
                onBlur={field.onBlur}
                ref={field.ref}
              />
            )}
          />
        )}
      </Field>
      <Field label="Parentesco" error={errors.relationship?.message} required>
        {(props) => (
          <Select {...props} defaultValue="" {...register('relationship')}>
            <option value="" disabled>
              Escolha
            </option>
            {relationshipOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        )}
      </Field>
      <div className="flex gap-2 sm:col-span-2 sm:justify-end">
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" isPending={add.isPending}>
          Salvar responsável
        </Button>
      </div>
    </form>
  )
}
