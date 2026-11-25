import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import type { SchoolYear } from '@/shared/api/types'
import { applyApiErrors } from '@/shared/lib/form'
import { Button } from '@/shared/ui/Button'
import { Dialog } from '@/shared/ui/Dialog'
import { Field, Input, RequiredFieldsNote } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { notify } from '@/shared/ui/toast.store'
import { useSaveSchoolYear } from '../api/school-years.queries'
import { SchoolYearSchema, type SchoolYearForm } from '../schemas/school-year.schema'

export function SchoolYearDialog({
  year,
  onClose,
}: {
  year: SchoolYear | null
  onClose: () => void
}) {
  const save = useSaveSchoolYear()
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<SchoolYearForm>({
    resolver: zodResolver(SchoolYearSchema),
    mode: 'onTouched',
    defaultValues: year
      ? { name: year.name, startsOn: year.startsOn, endsOn: year.endsOn, isCurrent: year.isCurrent }
      : { name: '', startsOn: '', endsOn: '', isCurrent: true },
  })

  const onSubmit = handleSubmit((data) => {
    setSummary(null)
    save.mutate(
      { id: year?.id, data },
      {
        onSuccess: () => {
          notify.success(year ? 'Ano letivo atualizado.' : 'Ano letivo cadastrado.')
          onClose()
        },
        onError: (error) =>
          setSummary(applyApiErrors(error, setError, ['name', 'startsOn', 'endsOn'])),
      },
    )
  })

  return (
    <Dialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={year ? 'Editar ano letivo' : 'Novo ano letivo'}
    >
      <form onSubmit={onSubmit} noValidate className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <RequiredFieldsNote />
        </div>
        <div className="sm:col-span-2">
          <FormErrorSummary message={summary} />
        </div>
        <Field label="Nome" error={errors.name?.message} required className="sm:col-span-2">
          {(props) => <Input {...props} placeholder="2026" {...register('name')} />}
        </Field>
        <Field label="Início" error={errors.startsOn?.message} required>
          {(props) => <Input {...props} type="date" {...register('startsOn')} />}
        </Field>
        <Field label="Término" error={errors.endsOn?.message} required>
          {(props) => <Input {...props} type="date" {...register('endsOn')} />}
        </Field>
        <label className="flex min-h-11 items-center gap-2 text-sm text-fg sm:col-span-2">
          <input type="checkbox" className="size-5 accent-primary" {...register('isCurrent')} />
          Ano letivo atual (usado no início e nos relatórios)
        </label>
        <div className="flex flex-col-reverse gap-2 sm:col-span-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isPending={save.isPending}>
            Salvar
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
