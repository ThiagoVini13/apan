import { zodResolver } from '@hookform/resolvers/zod'
import { useMemo, useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { useClassOptions } from '@/shared/api/reference'
import { todayIso } from '@/shared/lib/date'
import { applyApiErrors } from '@/shared/lib/form'
import { optionsFrom, relationshipLabels, shiftLabels } from '@/shared/lib/labels'
import { phoneDigits } from '@/shared/lib/phone'
import { useCurrentUser } from '@/shared/session/session'
import { Button } from '@/shared/ui/Button'
import { Dialog } from '@/shared/ui/Dialog'
import { Field, Input, RequiredFieldsNote, Select } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { PhoneInput } from '@/shared/ui/PhoneInput'
import { notify } from '@/shared/ui/toast.store'
import { useCreateStudent } from '../api/students.queries'
import { isMinor, makeStudentCreateSchema, type StudentCreateForm } from '../schemas/student.schema'

type StudentCreateDialogProps = { defaultClassId?: string; onClose: () => void }

const relationshipOptions = optionsFrom(relationshipLabels)

export function StudentCreateDialog({ defaultClassId, onClose }: StudentCreateDialogProps) {
  const user = useCurrentUser()
  const isTeacher = user.role === 'teacher'
  const classes = useClassOptions()
  const create = useCreateStudent()
  const [summary, setSummary] = useState<string | null>(null)
  const schema = useMemo(() => makeStudentCreateSchema({ requireClass: isTeacher }), [isTeacher])

  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<StudentCreateForm>({
    resolver: zodResolver(schema),
    mode: 'onTouched',
    defaultValues: {
      fullName: '',
      birthDate: '',
      classId: defaultClassId ?? '',
      guardianName: '',
      guardianPhone: '',
      guardianRelationship: '',
    },
  })
  const birthDate = useWatch({ control, name: 'birthDate' })
  const guardianRequired = isMinor(birthDate)

  const onSubmit = handleSubmit(
    (data) => {
      setSummary(null)
      const hasGuardian = !!data.guardianName
      create.mutate(
        {
          fullName: data.fullName,
          birthDate: data.birthDate,
          classId: data.classId || null,
          guardians:
            hasGuardian && data.guardianRelationship
              ? [
                  {
                    fullName: data.guardianName,
                    phone: phoneDigits(data.guardianPhone),
                    relationship: data.guardianRelationship,
                    isPrimary: true,
                  },
                ]
              : [],
        },
        {
          onSuccess: (student) => {
            notify.success(
              `${student.fullName} cadastrado(a). Matrícula ${student.enrollmentNumber}.`,
            )
            onClose()
          },
          onError: (error) =>
            setSummary(applyApiErrors(error, setError, ['fullName', 'birthDate', 'classId'])),
        },
      )
    },
    () => setSummary('Revise os campos destacados.'),
  )

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()} title="Novo aluno" size="lg">
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-5">
        <RequiredFieldsNote />
        <FormErrorSummary message={summary} />

        <fieldset className="grid gap-4 sm:grid-cols-2">
          <legend className="mb-2 font-semibold text-fg">Dados do aluno</legend>
          <Field
            label="Nome completo"
            error={errors.fullName?.message}
            required
            className="sm:col-span-2"
          >
            {(props) => <Input {...props} autoComplete="off" {...register('fullName')} />}
          </Field>
          <Field label="Data de nascimento" error={errors.birthDate?.message} required>
            {(props) => (
              <Input {...props} type="date" max={todayIso()} {...register('birthDate')} />
            )}
          </Field>
          <Field
            label="Turma"
            error={errors.classId?.message}
            required={isTeacher}
            hint={isTeacher ? undefined : 'Opcional: deixe em branco para matricular depois.'}
          >
            {(props) => (
              <Select {...props} {...register('classId')}>
                <option value="">{isTeacher ? 'Escolha a turma' : 'Sem turma por enquanto'}</option>
                {classes.data?.map((schoolClass) => (
                  <option key={schoolClass.id} value={schoolClass.id}>
                    {schoolClass.name} · {shiftLabels[schoolClass.shift]}
                  </option>
                ))}
              </Select>
            )}
          </Field>
        </fieldset>

        <fieldset className="grid gap-4 sm:grid-cols-2">
          <legend className="mb-2 font-semibold text-fg">
            Responsável {guardianRequired ? '(obrigatório para menores de 18 anos)' : '(opcional)'}
          </legend>
          <Field
            label="Nome do responsável"
            error={errors.guardianName?.message}
            required={guardianRequired}
            className="sm:col-span-2"
          >
            {(props) => <Input {...props} autoComplete="off" {...register('guardianName')} />}
          </Field>
          <Field label="Telefone" error={errors.guardianPhone?.message} required={guardianRequired}>
            {(props) => (
              <Controller
                control={control}
                name="guardianPhone"
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
          <Field
            label="Parentesco"
            error={errors.guardianRelationship?.message}
            required={guardianRequired}
          >
            {(props) => (
              <Select {...props} {...register('guardianRelationship')}>
                <option value="">Escolha</option>
                {relationshipOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            )}
          </Field>
        </fieldset>

        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isPending={create.isPending} pendingLabel="Cadastrando…">
            Cadastrar aluno
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
