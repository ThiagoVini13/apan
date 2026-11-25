import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useSchoolYears } from '@/shared/api/reference'
import type { SchoolClass } from '@/shared/api/types'
import { applyApiErrors } from '@/shared/lib/form'
import { optionsFrom, shiftLabels } from '@/shared/lib/labels'
import { Button } from '@/shared/ui/Button'
import { Dialog } from '@/shared/ui/Dialog'
import { Field, Input, RequiredFieldsNote, Select } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { notify } from '@/shared/ui/toast.store'
import { useSaveClass } from '../api/classes.queries'
import { ClassSchema, type ClassForm } from '../schemas/class.schema'

type ClassFormDialogProps = {
  schoolClass: SchoolClass | null
  defaultYearId?: string
  onClose: () => void
}

export function ClassFormDialog({ schoolClass, defaultYearId, onClose }: ClassFormDialogProps) {
  const years = useSchoolYears()
  const save = useSaveClass()
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<ClassForm>({
    resolver: zodResolver(ClassSchema),
    mode: 'onTouched',
    defaultValues: schoolClass
      ? {
          schoolYearId: schoolClass.schoolYearId,
          name: schoolClass.name,
          grade: schoolClass.grade,
          shift: schoolClass.shift,
          room: schoolClass.room ?? '',
          capacity: schoolClass.capacity ? String(schoolClass.capacity) : '',
        }
      : {
          schoolYearId: defaultYearId ?? '',
          name: '',
          grade: '',
          shift: 'morning',
          room: '',
          capacity: '',
        },
  })

  const onSubmit = handleSubmit((data) => {
    setSummary(null)
    save.mutate(
      {
        id: schoolClass?.id,
        data: {
          ...data,
          room: data.room || null,
          capacity: data.capacity ? Number(data.capacity) : null,
        },
      },
      {
        onSuccess: () => {
          notify.success(schoolClass ? 'Turma atualizada.' : 'Turma cadastrada.')
          onClose()
        },
        onError: (error) =>
          setSummary(
            applyApiErrors(error, setError, [
              'schoolYearId',
              'name',
              'grade',
              'shift',
              'room',
              'capacity',
            ]),
          ),
      },
    )
  })

  return (
    <Dialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={schoolClass ? 'Editar turma' : 'Nova turma'}
    >
      <form onSubmit={onSubmit} noValidate className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <RequiredFieldsNote />
        </div>
        <div className="sm:col-span-2">
          <FormErrorSummary message={summary} />
        </div>
        <Field
          label="Ano letivo"
          error={errors.schoolYearId?.message}
          required
          className="sm:col-span-2"
        >
          {(props) => (
            <Select {...props} disabled={!!schoolClass} {...register('schoolYearId')}>
              <option value="">Escolha</option>
              {years.data?.map((year) => (
                <option key={year.id} value={year.id}>
                  {year.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Nome" error={errors.name?.message} required>
          {(props) => <Input {...props} placeholder="5º Ano A" {...register('name')} />}
        </Field>
        <Field label="Série/etapa" error={errors.grade?.message} required>
          {(props) => <Input {...props} placeholder="5" {...register('grade')} />}
        </Field>
        <Field label="Turno" error={errors.shift?.message} required>
          {(props) => (
            <Select {...props} {...register('shift')}>
              {optionsFrom(shiftLabels).map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Sala" error={errors.room?.message}>
          {(props) => <Input {...props} {...register('room')} />}
        </Field>
        <Field
          label="Capacidade"
          hint="Número máximo de alunos (opcional)."
          error={errors.capacity?.message}
        >
          {(props) => <Input {...props} inputMode="numeric" {...register('capacity')} />}
        </Field>
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
