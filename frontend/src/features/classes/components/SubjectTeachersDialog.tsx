import { useEffect, useState } from 'react'
import { useSubjectOptions, useSubjectTeachers } from '@/shared/api/reference'
import type { SchoolClass } from '@/shared/api/types'
import { errorMessage } from '@/shared/lib/errors'
import { useTeachers } from '@/features/users'
import { Button } from '@/shared/ui/Button'
import { Dialog } from '@/shared/ui/Dialog'
import { Field, Select } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { PlusIcon, TrashIcon } from '@/shared/ui/icons'
import { LoadingList } from '@/shared/ui/States'
import { notify } from '@/shared/ui/toast.store'
import { useReplaceSubjectTeachers } from '../api/classes.queries'

type Row = { key: number; subjectId: string; teacherId: string }

let nextKey = 1

export function SubjectTeachersDialog({
  schoolClass,
  onClose,
}: {
  schoolClass: SchoolClass
  onClose: () => void
}) {
  const current = useSubjectTeachers(schoolClass.id)
  const subjects = useSubjectOptions()
  const teachers = useTeachers()
  const replace = useReplaceSubjectTeachers(schoolClass.id)
  const [rows, setRows] = useState<Row[] | null>(null)
  const [summary, setSummary] = useState<string | null>(null)

  useEffect(() => {
    if (current.data && rows === null) {
      setRows(
        current.data.map((item) => ({
          key: nextKey++,
          subjectId: item.subjectId,
          teacherId: item.teacherId,
        })),
      )
    }
  }, [current.data, rows])

  function updateRow(key: number, change: Partial<Row>) {
    setRows(
      (previous) => previous?.map((row) => (row.key === key ? { ...row, ...change } : row)) ?? null,
    )
  }

  function handleSave() {
    if (!rows) return
    setSummary(null)
    if (rows.some((row) => !row.subjectId || !row.teacherId)) {
      setSummary(
        'Escolha a disciplina e o(a) professor(a) em todas as linhas, ou remova as linhas vazias.',
      )
      return
    }
    const subjectIds = rows.map((row) => row.subjectId)
    if (new Set(subjectIds).size !== subjectIds.length) {
      setSummary('Cada disciplina pode aparecer só uma vez na turma.')
      return
    }
    replace.mutate(
      { items: rows.map(({ subjectId, teacherId }) => ({ subjectId, teacherId })) },
      {
        onSuccess: () => {
          notify.success('Professores da turma atualizados.')
          onClose()
        },
        onError: (error) => setSummary(errorMessage(error)),
      },
    )
  }

  return (
    <Dialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={`Professores de ${schoolClass.name}`}
      description="Cada professor(a) só enxerga as turmas e disciplinas vinculadas aqui."
      size="lg"
    >
      {rows === null ? (
        <LoadingList label="Carregando vínculos…" rows={2} />
      ) : (
        <div className="flex flex-col gap-4">
          <FormErrorSummary message={summary} />
          {rows.length === 0 && (
            <p className="text-sm text-fg-muted">Nenhuma disciplina vinculada a esta turma.</p>
          )}
          <ul className="flex flex-col gap-3">
            {rows.map((row, index) => (
              <li
                key={row.key}
                className="grid gap-3 rounded-lg border border-line p-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
              >
                <Field label={`Disciplina ${index + 1}`}>
                  {(props) => (
                    <Select
                      {...props}
                      value={row.subjectId}
                      onChange={(event) => updateRow(row.key, { subjectId: event.target.value })}
                    >
                      <option value="">Escolha</option>
                      {subjects.data?.map((subject) => (
                        <option key={subject.id} value={subject.id}>
                          {subject.name}
                        </option>
                      ))}
                    </Select>
                  )}
                </Field>
                <Field label={`Professor(a) da disciplina ${index + 1}`}>
                  {(props) => (
                    <Select
                      {...props}
                      value={row.teacherId}
                      onChange={(event) => updateRow(row.key, { teacherId: event.target.value })}
                    >
                      <option value="">Escolha</option>
                      {teachers.data?.map((teacher) => (
                        <option key={teacher.id} value={teacher.id}>
                          {teacher.fullName}
                        </option>
                      ))}
                    </Select>
                  )}
                </Field>
                <Button
                  variant="ghost"
                  aria-label={`Remover a linha ${index + 1}`}
                  onClick={() => setRows(rows.filter((item) => item.key !== row.key))}
                >
                  <TrashIcon className="size-4" />
                  Remover
                </Button>
              </li>
            ))}
          </ul>
          <Button
            variant="secondary"
            className="self-start"
            onClick={() => setRows([...rows, { key: nextKey++, subjectId: '', teacherId: '' }])}
          >
            <PlusIcon className="size-4" />
            Adicionar disciplina
          </Button>
          {teachers.data?.length === 0 && (
            <p className="text-sm text-fg-muted">
              Nenhum(a) professor(a) ativo(a). Convide em Administração › Usuários.
            </p>
          )}
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="secondary" onClick={onClose}>
              Cancelar
            </Button>
            <Button onClick={handleSave} isPending={replace.isPending}>
              Salvar vínculos
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  )
}
