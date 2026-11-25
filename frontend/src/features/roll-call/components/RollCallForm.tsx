import { useEffect, useId, useReducer, useRef, useState } from 'react'
import { useBlocker } from 'react-router-dom'
import type { RollCallSheet } from '@/shared/api/types'
import { MAX_NOTES_LENGTH } from '@/shared/lib/constants'
import { errorMessage } from '@/shared/lib/errors'
import { formatDate } from '@/shared/lib/format'
import { Button } from '@/shared/ui/Button'
import { ConfirmDialog } from '@/shared/ui/Dialog'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { CheckIcon, InfoIcon } from '@/shared/ui/icons'
import { EmptyState } from '@/shared/ui/States'
import { notify } from '@/shared/ui/toast.store'
import { useSaveRollCall } from '../api/roll-call.queries'
import { countMarks, draftReducer, firstPending, initialDraft } from '../lib/draft'
import { StudentMarkRow } from './StudentMarkRow'

type RollCallFormProps = { sheet: RollCallSheet; lockedReason: string | null }

export function RollCallForm({ sheet, lockedReason }: RollCallFormProps) {
  const [draft, dispatch] = useReducer(draftReducer, sheet, initialDraft)
  const [summary, setSummary] = useState<string | null>(null)
  const listRef = useRef<HTMLUListElement>(null)
  const notesId = useId()
  const save = useSaveRollCall()
  const counts = countMarks(draft.marks)
  const isLocked = lockedReason !== null
  const hasUnsavedChanges = draft.isDirty && !save.isSuccess

  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      hasUnsavedChanges && currentLocation.pathname !== nextLocation.pathname,
  )

  useEffect(() => {
    if (!hasUnsavedChanges) return
    const handler = (event: BeforeUnloadEvent) => event.preventDefault()
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [hasUnsavedChanges])

  function focusStudent(studentId: string) {
    listRef.current
      ?.querySelector<HTMLButtonElement>(`[data-student-id="${studentId}"] button`)
      ?.focus()
  }

  function handleSave() {
    setSummary(null)
    const pending = firstPending(
      sheet.students.map((s) => s.studentId),
      draft.marks,
    )
    if (pending) {
      setSummary(
        counts.pending === 1
          ? 'Falta marcar 1 aluno antes de salvar.'
          : `Faltam marcar ${counts.pending} alunos antes de salvar.`,
      )
      focusStudent(pending)
      return
    }
    save.mutate(
      {
        classId: sheet.classId,
        subjectId: sheet.subjectId,
        lessonDate: sheet.lessonDate,
        notes: draft.notes.trim() || null,
        attendances: sheet.students.map((s) => ({
          studentId: s.studentId,
          status: draft.marks[s.studentId] ?? 'present',
        })),
      },
      {
        onSuccess: () => notify.success(`Chamada de ${formatDate(sheet.lessonDate)} salva.`),
        onError: (error) => setSummary(errorMessage(error)),
      },
    )
  }

  if (sheet.students.length === 0) {
    return (
      <EmptyState
        title="Nenhum aluno matriculado nesta data"
        description="Confira a turma e a data, ou matricule alunos na turma."
      />
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {isLocked && (
        <p className="flex items-start gap-2 rounded-lg border border-warning bg-warning-bg p-3 text-sm text-fg">
          <InfoIcon className="mt-0.5 size-4 text-warning" />
          {lockedReason}
        </p>
      )}

      {!isLocked && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-fg-muted">
            Marque Presente ou Ausente para cada aluno. Use Tab para avançar e Espaço para marcar.
          </p>
          <Button variant="secondary" onClick={() => dispatch({ type: 'markAllPresent' })}>
            <CheckIcon className="size-4" />
            Marcar todos como presentes
          </Button>
        </div>
      )}

      <section aria-label="Lista de alunos" className="rounded-xl border border-line bg-surface">
        <ul ref={listRef}>
          {sheet.students.map((student) => (
            <StudentMarkRow
              key={student.studentId}
              student={student}
              status={draft.marks[student.studentId] ?? null}
              disabled={isLocked}
              onMark={(status) => dispatch({ type: 'mark', studentId: student.studentId, status })}
            />
          ))}
        </ul>
      </section>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={notesId} className="text-sm font-medium text-fg">
          Anotações da aula
        </label>
        <textarea
          id={notesId}
          value={draft.notes}
          maxLength={MAX_NOTES_LENGTH}
          disabled={isLocked}
          onChange={(event) => dispatch({ type: 'notes', value: event.target.value })}
          aria-describedby={`${notesId}-count`}
          placeholder="Conteúdo trabalhado, ocorrências, recados…"
          className="min-h-28 w-full rounded-lg border border-line-strong bg-surface px-3 py-2 text-base text-fg placeholder:text-fg-muted disabled:opacity-60"
        />
        <p id={`${notesId}-count`} className="text-right text-sm text-fg-muted tabular-nums">
          {draft.notes.length} de {MAX_NOTES_LENGTH} caracteres
        </p>
      </div>

      <FormErrorSummary message={summary} />

      <div className="sticky bottom-16 z-20 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-surface p-3 shadow-lg lg:bottom-4">
        <p role="status" aria-live="polite" className="text-sm font-medium text-fg tabular-nums">
          <span className="text-success">{counts.present} presentes</span>
          {' · '}
          <span className="text-danger">{counts.absent} ausentes</span>
          {' · '}
          <span>{counts.pending} sem marcação</span>
        </p>
        {!isLocked && (
          <Button onClick={handleSave} isPending={save.isPending} pendingLabel="Salvando…">
            Salvar frequência
          </Button>
        )}
      </div>

      <ConfirmDialog
        open={blocker.state === 'blocked'}
        onOpenChange={(open) => !open && blocker.reset?.()}
        title="Sair sem salvar?"
        description="As marcações e anotações desta chamada ainda não foram salvas."
        confirmLabel="Sair sem salvar"
        tone="danger"
        onConfirm={() => blocker.proceed?.()}
      />
    </div>
  )
}
