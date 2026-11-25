import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import type { Subject } from '@/shared/api/types'
import { applyApiErrors } from '@/shared/lib/form'
import { Button } from '@/shared/ui/Button'
import { Dialog } from '@/shared/ui/Dialog'
import { Field, Input, RequiredFieldsNote } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { notify } from '@/shared/ui/toast.store'
import { useSaveSubject } from '../api/subjects.queries'
import { SubjectSchema, type SubjectForm } from '../schemas/subject.schema'

export function SubjectDialog({
  subject,
  onClose,
}: {
  subject: Subject | null
  onClose: () => void
}) {
  const save = useSaveSubject()
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<SubjectForm>({
    resolver: zodResolver(SubjectSchema),
    mode: 'onTouched',
    defaultValues: subject ? { name: subject.name, code: subject.code } : { name: '', code: '' },
  })

  const onSubmit = handleSubmit((data) => {
    setSummary(null)
    save.mutate(
      { id: subject?.id, data },
      {
        onSuccess: () => {
          notify.success(subject ? 'Disciplina atualizada.' : 'Disciplina cadastrada.')
          onClose()
        },
        onError: (error) => setSummary(applyApiErrors(error, setError, ['name', 'code'])),
      },
    )
  })

  return (
    <Dialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={subject ? 'Editar disciplina' : 'Nova disciplina'}
    >
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        <RequiredFieldsNote />
        <FormErrorSummary message={summary} />
        <Field label="Nome" error={errors.name?.message} required>
          {(props) => <Input {...props} {...register('name')} />}
        </Field>
        <Field
          label="Código"
          hint="Sigla curta usada em listas, por exemplo MAT."
          error={errors.code?.message}
          required
        >
          {(props) => <Input {...props} className="uppercase" {...register('code')} />}
        </Field>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
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
