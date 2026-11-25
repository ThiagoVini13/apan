import { useClassOptions, useCurrentSchoolYear, useSubjectOptions } from '@/shared/api/reference'
import type { ExportFormat } from '@/shared/api/types'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { useSearchParamsState } from '@/shared/hooks/useSearchParamsState'
import { cn } from '@/shared/lib/cn'
import { MIN_ATTENDANCE_RATE } from '@/shared/lib/constants'
import { isIsoDate, todayIso } from '@/shared/lib/date'
import { formatDate, formatPercent } from '@/shared/lib/format'
import { shiftLabels } from '@/shared/lib/labels'
import { AttendanceRateBadge } from '@/shared/ui/Badge'
import { Button } from '@/shared/ui/Button'
import { Field, Input, Select } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { DownloadIcon } from '@/shared/ui/icons'
import { Card, PageHeader, Stat, TableContainer } from '@/shared/ui/Layout'
import { tableClasses } from '@/shared/ui/table'
import { EmptyState, ErrorState, LoadingList } from '@/shared/ui/States'
import { notify } from '@/shared/ui/toast.store'
import {
  useExportReport,
  useReportByClass,
  useReportStudents,
  useReportSummary,
  useTerms,
} from '../api/reports.queries'
import { ClassChart } from '../components/ClassChart'
import { defaultPeriod, periodShortcuts } from '../lib/periods'
import type { ReportParams } from '../types'

const KEYS = ['from', 'to', 'classId', 'subjectId', 'risk'] as const

export default function ReportsPage() {
  useDocumentTitle('Relatórios')
  const today = todayIso()
  const [params, setParams] = useSearchParamsState(KEYS)
  const classes = useClassOptions()
  const subjects = useSubjectOptions()
  const year = useCurrentSchoolYear()
  const terms = useTerms(year.data?.id)
  const exportReport = useExportReport()

  const fallback = defaultPeriod(today)
  const from = isIsoDate(params.from) ? params.from : fallback.from
  const to = isIsoDate(params.to) ? params.to : fallback.to
  const rangeError = to < from ? 'A data final deve ser igual ou posterior à data inicial.' : null

  const reportParams: ReportParams | null = rangeError
    ? null
    : { from, to, classId: params.classId || undefined, subjectId: params.subjectId || undefined }

  const summary = useReportSummary(reportParams)
  const students = useReportStudents(reportParams)
  const byClass = useReportByClass(reportParams)
  const shortcuts = periodShortcuts(today, year.data, terms.data ?? [])
  const onlyAtRisk = params.risk === '1'
  const visibleStudents = (students.data ?? []).filter((row) => !onlyAtRisk || row.atRisk)

  function handleExport(format: ExportFormat) {
    if (!reportParams) return
    exportReport.mutate(
      { params: reportParams, format },
      { onSuccess: () => notify.success(`Planilha ${format.toUpperCase()} gerada.`) },
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Relatórios"
        description="Frequência total por período, turma e disciplina."
        actions={
          <>
            <Button
              onClick={() => handleExport('xlsx')}
              disabled={!reportParams}
              isPending={exportReport.isPending && exportReport.variables?.format === 'xlsx'}
            >
              <DownloadIcon className="size-4" />
              Exportar XLSX
            </Button>
            <Button
              variant="secondary"
              onClick={() => handleExport('csv')}
              disabled={!reportParams}
              isPending={exportReport.isPending && exportReport.variables?.format === 'csv'}
            >
              <DownloadIcon className="size-4" />
              Exportar CSV
            </Button>
          </>
        }
      />

      <Card aria-label="Filtros do relatório">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Data inicial">
            {(props) => (
              <Input
                {...props}
                type="date"
                value={from}
                onChange={(event) => setParams({ from: event.target.value })}
              />
            )}
          </Field>
          <Field label="Data final" error={rangeError ?? undefined}>
            {(props) => (
              <Input
                {...props}
                type="date"
                value={to}
                onChange={(event) => setParams({ to: event.target.value })}
              />
            )}
          </Field>
          <Field label="Turma">
            {(props) => (
              <Select
                {...props}
                value={params.classId}
                onChange={(event) => setParams({ classId: event.target.value })}
              >
                <option value="">Todas as turmas</option>
                {classes.data?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} · {shiftLabels[c.shift]}
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
              >
                <option value="">Todas as disciplinas</option>
                {subjects.data?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
            )}
          </Field>
        </div>
        <div role="group" aria-label="Atalhos de período" className="mt-4 flex flex-wrap gap-2">
          {shortcuts.map((shortcut) => {
            const isActive = shortcut.from === from && shortcut.to === to
            return (
              <Button
                key={shortcut.label}
                variant={isActive ? 'primary' : 'secondary'}
                aria-pressed={isActive}
                onClick={() => setParams({ from: shortcut.from, to: shortcut.to })}
              >
                {shortcut.label}
              </Button>
            )
          })}
        </div>
      </Card>

      <FormErrorSummary message={rangeError} />
      {exportReport.isError && (
        <ErrorState error={exportReport.error} title="Não foi possível gerar a planilha" />
      )}

      {summary.isPending && reportParams && (
        <LoadingList label="Calculando o relatório…" rows={2} />
      )}
      {summary.isError && <ErrorState error={summary.error} onRetry={() => summary.refetch()} />}
      {summary.data && (
        <section aria-labelledby="totals-heading" className="flex flex-col gap-3">
          <h2 id="totals-heading" className="text-lg font-bold text-fg">
            Totais de {formatDate(from)} a {formatDate(to)}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Stat
              label="Frequência geral"
              value={formatPercent(summary.data.attendanceRate)}
              tone={
                summary.data.attendanceRate !== null &&
                summary.data.attendanceRate < MIN_ATTENDANCE_RATE
                  ? 'danger'
                  : 'default'
              }
              hint={`Mínimo exigido: ${MIN_ATTENDANCE_RATE}%`}
            />
            <Stat
              label="Presenças"
              value={summary.data.present}
              hint={`Faltas: ${summary.data.absent}`}
            />
            <Stat
              label="Aulas registradas"
              value={summary.data.lessons}
              hint={
                summary.data.schoolDays !== null
                  ? `${summary.data.schoolDays} dias letivos no período`
                  : undefined
              }
            />
            <Stat label="Alunos com aulas" value={summary.data.students} />
            <Stat
              label={`Alunos abaixo de ${MIN_ATTENDANCE_RATE}%`}
              value={summary.data.atRiskStudents}
              tone={summary.data.atRiskStudents > 0 ? 'danger' : 'success'}
            />
          </div>
        </section>
      )}

      {byClass.data && byClass.data.length > 0 && (
        <Card aria-labelledby="by-class-heading">
          <h2 id="by-class-heading" className="mb-4 text-lg font-bold text-fg">
            Presença por turma
          </h2>
          <ClassChart rows={byClass.data} />
        </Card>
      )}

      {students.data && (
        <section aria-labelledby="students-heading" className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 id="students-heading" className="text-lg font-bold text-fg">
              Frequência por aluno
            </h2>
            <label className="flex min-h-11 items-center gap-2 text-sm text-fg">
              <input
                type="checkbox"
                className="size-5 accent-primary"
                checked={onlyAtRisk}
                onChange={(event) => setParams({ risk: event.target.checked ? '1' : null })}
              />
              Mostrar só alunos abaixo de {MIN_ATTENDANCE_RATE}%
            </label>
          </div>
          <p role="status" aria-live="polite" className="text-sm text-fg-muted">
            {visibleStudents.length} aluno(s) na lista
          </p>
          {visibleStudents.length === 0 ? (
            <EmptyState
              title={onlyAtRisk ? 'Nenhum aluno abaixo do mínimo' : 'Nenhuma chamada no período'}
              description={onlyAtRisk ? undefined : 'Escolha outro período ou turma.'}
            />
          ) : (
            <TableContainer label="Tabela de frequência por aluno">
              <table className={tableClasses.table}>
                <thead className={tableClasses.head}>
                  <tr>
                    <th scope="col" className={tableClasses.th}>
                      Aluno
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      Matrícula
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      Turma
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      Presenças
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      Faltas
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      Aulas
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      Frequência
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {visibleStudents.map((row) => (
                    <tr key={`${row.studentId}-${row.classId}`} className={tableClasses.row}>
                      <th scope="row" className={cn(tableClasses.td, 'font-medium')}>
                        {row.fullName}
                      </th>
                      <td className={cn(tableClasses.td, 'tabular-nums')}>
                        {row.enrollmentNumber}
                      </td>
                      <td className={tableClasses.td}>{row.className}</td>
                      <td className={cn(tableClasses.td, 'tabular-nums')}>{row.present}</td>
                      <td className={cn(tableClasses.td, 'tabular-nums')}>{row.absent}</td>
                      <td className={cn(tableClasses.td, 'tabular-nums')}>{row.total}</td>
                      <td className={tableClasses.td}>
                        <AttendanceRateBadge rate={row.attendanceRate} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableContainer>
          )}
        </section>
      )}
    </div>
  )
}
