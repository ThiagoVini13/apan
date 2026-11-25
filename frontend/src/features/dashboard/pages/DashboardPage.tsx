import { Link } from 'react-router-dom'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { cn } from '@/shared/lib/cn'
import { formatDateLong, formatPercent } from '@/shared/lib/format'
import { useCurrentUser } from '@/shared/session/session'
import { AttendanceRateBadge } from '@/shared/ui/Badge'
import { buttonVariants } from '@/shared/ui/button-variants'
import { ChartIcon, CheckIcon, ClipboardIcon, PlusIcon } from '@/shared/ui/icons'
import { Card, PageHeader, Stat } from '@/shared/ui/Layout'
import { EmptyState, ErrorState, Skeleton } from '@/shared/ui/States'
import { useDashboardToday } from '../api/dashboard.queries'

export default function DashboardPage() {
  useDocumentTitle('Início')
  const user = useCurrentUser()
  const { data, isPending, isError, error, refetch } = useDashboardToday()

  const firstName = user.fullName.split(' ')[0]

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={`Olá, ${firstName}`}
        description={data ? formatDateLong(data.date) : undefined}
        actions={
          <>
            <Link to="/roll-call" className={buttonVariants()}>
              <ClipboardIcon className="size-4" />
              Fazer chamada
            </Link>
            <Link to="/students/new" className={buttonVariants({ variant: 'secondary' })}>
              <PlusIcon className="size-4" />
              Adicionar aluno
            </Link>
            <Link to="/reports" className={buttonVariants({ variant: 'secondary' })}>
              <ChartIcon className="size-4" />
              Extrair relatório
            </Link>
          </>
        }
      />

      {isPending && (
        <div aria-busy="true" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <span className="sr-only">Carregando o resumo do dia…</span>
          {[1, 2, 3, 4].map((key) => (
            <Skeleton key={key} className="h-28" />
          ))}
        </div>
      )}
      {isError && <ErrorState error={error} onRetry={() => refetch()} />}

      {data && !data.schoolYearId && (
        <EmptyState
          title="Nenhum ano letivo atual"
          description="A administração precisa cadastrar o ano letivo e marcá-lo como atual."
        />
      )}

      {data?.schoolYearId && (
        <>
          <section aria-labelledby="summary-heading">
            <h2 id="summary-heading" className="sr-only">
              Resumo
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Stat label="Turmas ativas" value={data.totalClasses} hint={data.schoolYearName} />
              <Stat label="Alunos matriculados" value={data.totalStudents} />
              <Stat
                label="Chamadas de hoje"
                value={`${data.rollCallsDone} de ${data.rollCallsExpected}`}
                hint={data.isSchoolDay ? 'Dia letivo' : 'Hoje não é dia letivo'}
              />
              <Stat
                label="Presença nos últimos 30 dias"
                value={formatPercent(data.presenceRateLast30Days)}
                hint={`Hoje: ${formatPercent(data.presenceRateToday)}`}
              />
            </div>
          </section>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card aria-labelledby="pending-heading">
              <h2 id="pending-heading" className="text-lg font-bold text-fg">
                Chamadas pendentes hoje
              </h2>
              {data.pendingRollCalls.length === 0 ? (
                <p className="mt-3 flex items-center gap-2 text-fg-muted">
                  <CheckIcon className="size-4 text-success" />
                  {data.isSchoolDay
                    ? 'Todas as chamadas de hoje foram feitas.'
                    : 'Não há aulas hoje.'}
                </p>
              ) : (
                <ul className="mt-3 flex flex-col gap-2">
                  {data.pendingRollCalls.map((item) => (
                    <li key={`${item.classId}-${item.subjectId}`}>
                      <Link
                        to={`/roll-call?classId=${item.classId}&subjectId=${item.subjectId}&date=${data.date}`}
                        className={cn(
                          'flex min-h-11 flex-wrap items-center justify-between gap-2 rounded-lg border border-line px-3 py-2 hover:bg-surface-muted',
                        )}
                      >
                        <span className="font-medium text-fg">
                          {item.className} · {item.subjectName}
                        </span>
                        <span className="text-sm text-fg-muted">
                          {user.role === 'admin' ? item.teacherName : 'Fazer chamada'}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card aria-labelledby="risk-heading">
              <h2 id="risk-heading" className="text-lg font-bold text-fg">
                Alunos abaixo de 75% no ano
              </h2>
              {data.lowAttendanceStudents.length === 0 ? (
                <p className="mt-3 flex items-center gap-2 text-fg-muted">
                  <CheckIcon className="size-4 text-success" />
                  Nenhum aluno abaixo do mínimo.
                </p>
              ) : (
                <ul className="mt-3 flex flex-col gap-2">
                  {data.lowAttendanceStudents.map((student) => (
                    <li
                      key={`${student.studentId}-${student.classId}`}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-line px-3 py-2"
                    >
                      <span>
                        <span className="font-medium text-fg">{student.fullName}</span>
                        <span className="text-sm text-fg-muted"> · {student.className}</span>
                      </span>
                      <AttendanceRateBadge rate={student.attendanceRate} />
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
