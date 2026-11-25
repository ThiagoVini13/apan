import { useEffect, useMemo } from 'react'
import { useClassOptions, useSubjectOptions, useSubjectTeachers } from '@/shared/api/reference'
import type { RollCallSheet } from '@/shared/api/types'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { useSearchParamsState } from '@/shared/hooks/useSearchParamsState'
import { isIsoDate, todayIso } from '@/shared/lib/date'
import { shiftLabels } from '@/shared/lib/labels'
import { useCurrentUser } from '@/shared/session/session'
import { Field, Input, Select } from '@/shared/ui/Field'
import { Card, PageHeader } from '@/shared/ui/Layout'
import { EmptyState, ErrorState, LoadingList } from '@/shared/ui/States'
import { useRollCallSheet } from '../api/roll-call.queries'
import { RollCallForm } from '../components/RollCallForm'

const KEYS = ['classId', 'subjectId', 'date'] as const

function lockedReason(sheet: RollCallSheet, isAdmin: boolean): string | null {
  if (!sheet.isSchoolDay) return 'Esta data não é dia letivo no calendário da escola.'
  if (!sheet.editable) {
    return isAdmin
      ? 'Esta turma está arquivada. A chamada fica disponível só para consulta.'
      : 'O prazo para registrar ou alterar esta chamada terminou. Fale com a coordenação se precisar corrigir.'
  }
  return null
}

export default function RollCallPage() {
  useDocumentTitle('Chamada')
  const user = useCurrentUser()
  const isAdmin = user.role === 'admin'
  const [params, setParams] = useSearchParamsState(KEYS)
  const today = todayIso()
  const date = isIsoDate(params.date) && params.date <= today ? params.date : today

  const classes = useClassOptions()
  const assignments = useSubjectTeachers(params.classId || undefined)
  const allSubjects = useSubjectOptions()

  const subjectOptions = useMemo(() => {
    const assigned = (assignments.data ?? []).filter((a) => isAdmin || a.teacherId === user.id)
    if (assigned.length > 0 || !isAdmin) {
      return assigned.map((a) => ({
        id: a.subjectId,
        label: `${a.subjectName} (${a.teacherName})`,
      }))
    }
    return (allSubjects.data ?? []).map((s) => ({ id: s.id, label: s.name }))
  }, [assignments.data, allSubjects.data, isAdmin, user.id])

  useEffect(() => {
    const firstClass = classes.data?.[0]
    if (!params.classId && firstClass) setParams({ classId: firstClass.id }, { resetPage: false })
  }, [classes.data, params.classId, setParams])

  useEffect(() => {
    if (!params.classId || !assignments.isSuccess) return
    const valid = subjectOptions.some((option) => option.id === params.subjectId)
    if (!valid) setParams({ subjectId: subjectOptions[0]?.id ?? null }, { resetPage: false })
  }, [params.classId, params.subjectId, subjectOptions, assignments.isSuccess, setParams])

  const sheetParams =
    params.classId && params.subjectId
      ? { classId: params.classId, subjectId: params.subjectId, date }
      : null
  const sheet = useRollCallSheet(sheetParams)
  const selectedClass = classes.data?.find((c) => c.id === params.classId)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Chamada" description="Escolha a turma, a disciplina e a data da aula." />

      <Card aria-label="Filtros da chamada">
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Turma">
            {(props) => (
              <Select
                {...props}
                value={params.classId}
                onChange={(event) => setParams({ classId: event.target.value, subjectId: null })}
                disabled={!classes.data?.length}
              >
                {classes.data?.map((schoolClass) => (
                  <option key={schoolClass.id} value={schoolClass.id}>
                    {schoolClass.name} · {shiftLabels[schoolClass.shift]}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Disciplina">
            {(props) => (
              <Select
                {...props}
                value={params.subjectId}
                onChange={(event) => setParams({ subjectId: event.target.value })}
                disabled={subjectOptions.length === 0}
              >
                {subjectOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Data da aula">
            {(props) => (
              <Input
                {...props}
                type="date"
                value={date}
                max={today}
                onChange={(event) => setParams({ date: event.target.value || null })}
              />
            )}
          </Field>
        </div>
      </Card>

      {classes.isSuccess && classes.data.length === 0 && (
        <EmptyState
          title="Nenhuma turma disponível"
          description={
            isAdmin
              ? 'Cadastre turmas em Administração › Turmas.'
              : 'Você ainda não está vinculado(a) a nenhuma turma. Fale com a coordenação.'
          }
        />
      )}
      {params.classId && assignments.isSuccess && subjectOptions.length === 0 && (
        <EmptyState
          title="Nenhuma disciplina para esta turma"
          description="A administração precisa vincular disciplinas e professores à turma."
        />
      )}
      {classes.isError && <ErrorState error={classes.error} onRetry={() => classes.refetch()} />}

      {sheet.isPending && sheetParams && (
        <LoadingList label="Carregando a lista de alunos…" rows={6} />
      )}
      {sheet.isError && <ErrorState error={sheet.error} onRetry={() => sheet.refetch()} />}
      {sheet.data && (
        <section aria-labelledby="sheet-heading" className="flex flex-col gap-3">
          <h2 id="sheet-heading" className="text-lg font-bold text-fg">
            {selectedClass?.name ?? 'Turma'} · {sheet.data.students.length} alunos
            {sheet.data.rollCallId && (
              <span className="font-normal text-fg-muted"> · chamada já registrada</span>
            )}
          </h2>
          <RollCallForm
            key={`${sheet.dataUpdatedAt}-${date}`}
            sheet={sheet.data}
            lockedReason={lockedReason(sheet.data, isAdmin)}
          />
        </section>
      )}
    </div>
  )
}
