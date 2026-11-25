import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useClassOptions } from '@/shared/api/reference'
import type { StudentDetail } from '@/shared/api/types'
import { todayIso } from '@/shared/lib/date'
import { errorMessage } from '@/shared/lib/errors'
import { applyApiErrors } from '@/shared/lib/form'
import { formatDateTime } from '@/shared/lib/format'
import { shiftLabels } from '@/shared/lib/labels'
import { useCurrentUser } from '@/shared/session/session'
import { Badge } from '@/shared/ui/Badge'
import { Button } from '@/shared/ui/Button'
import { ConfirmDialog, Dialog } from '@/shared/ui/Dialog'
import { Field, Input, Select } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { ArchiveIcon } from '@/shared/ui/icons'
import { ErrorState, LoadingList } from '@/shared/ui/States'
import { notify } from '@/shared/ui/toast.store'
import {
  useArchiveStudent,
  useEnrollStudent,
  useStudent,
  useTransferStudent,
  useUpdateStudent,
} from '../api/students.queries'
import { StudentUpdateSchema, type StudentUpdateForm } from '../schemas/student.schema'
import { GuardiansSection } from './GuardiansSection'

type StudentEditDialogProps = { studentId: string; onClose: () => void }

export function StudentEditDialog({ studentId, onClose }: StudentEditDialogProps) {
  const { data: student, isPending, isError, error, refetch } = useStudent(studentId)

  return (
    <Dialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={student ? student.fullName : 'Aluno'}
      description={student ? `Matrícula ${student.enrollmentNumber}` : undefined}
      size="lg"
    >
      {isPending && <LoadingList label="Carregando os dados do aluno…" rows={3} />}
      {isError && <ErrorState error={error} onRetry={() => refetch()} />}
      {student && <StudentEditContent student={student} onClose={onClose} />}
    </Dialog>
  )
}

function StudentEditContent({ student, onClose }: { student: StudentDetail; onClose: () => void }) {
  const user = useCurrentUser()
  const isAdmin = user.role === 'admin'
  const isArchived = student.archivedAt !== null

  return (
    <div className="flex flex-col gap-6">
      {isArchived && (
        <Badge tone="warning" icon={<ArchiveIcon className="size-3.5" />} className="self-start">
          Arquivado em {formatDateTime(student.archivedAt as string)}
        </Badge>
      )}
      <StudentDataForm student={student} disabled={isArchived} />
      <GuardiansSection
        studentId={student.id}
        guardians={student.guardians}
        disabled={isArchived}
      />
      {isAdmin && !isArchived && <EnrollmentSection student={student} />}
      {isAdmin && !isArchived && <ArchiveSection student={student} onArchived={onClose} />}
    </div>
  )
}

function StudentDataForm({ student, disabled }: { student: StudentDetail; disabled: boolean }) {
  const update = useUpdateStudent(student.id)
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isDirty },
    reset,
  } = useForm<StudentUpdateForm>({
    resolver: zodResolver(StudentUpdateSchema),
    mode: 'onTouched',
    defaultValues: { fullName: student.fullName, birthDate: student.birthDate },
  })

  const onSubmit = handleSubmit((data) => {
    setSummary(null)
    update.mutate(data, {
      onSuccess: (saved) => {
        reset({ fullName: saved.fullName, birthDate: saved.birthDate })
        notify.success('Dados do aluno atualizados.')
      },
      onError: (error) => setSummary(applyApiErrors(error, setError, ['fullName', 'birthDate'])),
    })
  })

  return (
    <form
      onSubmit={onSubmit}
      noValidate
      aria-labelledby="student-data-heading"
      className="flex flex-col gap-4"
    >
      <h3 id="student-data-heading" className="font-semibold text-fg">
        Dados do aluno
      </h3>
      <FormErrorSummary message={summary} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          label="Nome completo"
          error={errors.fullName?.message}
          required
          className="sm:col-span-2"
        >
          {(props) => (
            <Input {...props} disabled={disabled} autoComplete="off" {...register('fullName')} />
          )}
        </Field>
        <Field label="Data de nascimento" error={errors.birthDate?.message} required>
          {(props) => (
            <Input
              {...props}
              type="date"
              max={todayIso()}
              disabled={disabled}
              {...register('birthDate')}
            />
          )}
        </Field>
      </div>
      {!disabled && (
        <Button
          type="submit"
          variant="secondary"
          disabled={!isDirty}
          isPending={update.isPending}
          className="self-start"
        >
          Salvar dados
        </Button>
      )}
    </form>
  )
}

function EnrollmentSection({ student }: { student: StudentDetail }) {
  const classes = useClassOptions()
  const transfer = useTransferStudent()
  const enroll = useEnrollStudent()
  const [classId, setClassId] = useState('')
  const [transferOn, setTransferOn] = useState(todayIso())
  const [summary, setSummary] = useState<string | null>(null)
  const current = classes.data?.find((c) => c.id === student.currentClassId)
  const isEnrolled = !!student.currentEnrollmentId

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setSummary(null)
    if (!classId) {
      setSummary('Escolha a turma de destino.')
      return
    }
    const onError = (error: unknown) => setSummary(errorMessage(error))
    if (isEnrolled) {
      transfer.mutate(
        { enrollmentId: student.currentEnrollmentId as string, classId, transferOn },
        { onSuccess: () => notify.success('Transferência registrada.'), onError },
      )
    } else {
      enroll.mutate(
        { studentId: student.id, classId },
        { onSuccess: () => notify.success('Matrícula registrada.'), onError },
      )
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      aria-labelledby="enrollment-heading"
      className="flex flex-col gap-3"
    >
      <h3 id="enrollment-heading" className="font-semibold text-fg">
        Matrícula
      </h3>
      <p className="text-sm text-fg-muted">
        {current
          ? `Turma atual: ${current.name} · ${shiftLabels[current.shift]}`
          : 'Sem matrícula ativa.'}
      </p>
      <FormErrorSummary message={summary} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={isEnrolled ? 'Transferir para a turma' : 'Matricular na turma'}>
          {(props) => (
            <Select {...props} value={classId} onChange={(event) => setClassId(event.target.value)}>
              <option value="">Escolha</option>
              {classes.data
                ?.filter((c) => c.id !== student.currentClassId)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} · {shiftLabels[c.shift]}
                  </option>
                ))}
            </Select>
          )}
        </Field>
        {isEnrolled && (
          <Field label="A partir de">
            {(props) => (
              <Input
                {...props}
                type="date"
                value={transferOn}
                onChange={(event) => setTransferOn(event.target.value)}
              />
            )}
          </Field>
        )}
      </div>
      <Button
        type="submit"
        variant="secondary"
        className="self-start"
        isPending={transfer.isPending || enroll.isPending}
      >
        {isEnrolled ? 'Transferir' : 'Matricular'}
      </Button>
    </form>
  )
}

function ArchiveSection({
  student,
  onArchived,
}: {
  student: StudentDetail
  onArchived: () => void
}) {
  const [isConfirming, setIsConfirming] = useState(false)
  const archive = useArchiveStudent(student.id)
  return (
    <section
      aria-labelledby="archive-heading"
      className="flex flex-col gap-2 border-t border-line pt-4"
    >
      <h3 id="archive-heading" className="font-semibold text-fg">
        Arquivar
      </h3>
      <p className="text-sm text-fg-muted">
        Use quando o aluno deixar a escola. A matrícula ativa é encerrada e o histórico de
        frequência é mantido.
      </p>
      <Button variant="danger" className="self-start" onClick={() => setIsConfirming(true)}>
        <ArchiveIcon className="size-4" />
        Arquivar aluno
      </Button>
      <ConfirmDialog
        open={isConfirming}
        onOpenChange={setIsConfirming}
        title={`Arquivar ${student.fullName}?`}
        description="O aluno deixa de aparecer nas listas e nas chamadas. O histórico continua nos relatórios."
        confirmLabel="Arquivar"
        tone="danger"
        isPending={archive.isPending}
        onConfirm={() =>
          archive.mutate(undefined, {
            onSuccess: () => {
              notify.success(`${student.fullName} foi arquivado(a).`)
              onArchived()
            },
          })
        }
      />
    </section>
  )
}
