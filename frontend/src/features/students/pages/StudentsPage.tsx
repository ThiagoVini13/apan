import { useState, type FormEvent } from 'react'
import { Link, Outlet, useLocation, useNavigate, useParams } from 'react-router-dom'
import { useClassOptions, useCurrentSchoolYear } from '@/shared/api/reference'
import type { Student } from '@/shared/api/types'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { useSearchParamsState } from '@/shared/hooks/useSearchParamsState'
import { cn } from '@/shared/lib/cn'
import { calculateAge, todayIso } from '@/shared/lib/date'
import { formatDate } from '@/shared/lib/format'
import { shiftLabels } from '@/shared/lib/labels'
import { useCurrentUser } from '@/shared/session/session'
import { AttendanceRateBadge, Badge } from '@/shared/ui/Badge'
import { Button } from '@/shared/ui/Button'
import { buttonVariants } from '@/shared/ui/button-variants'
import { Field, Input, Select } from '@/shared/ui/Field'
import { ArchiveIcon, PencilIcon, PlusIcon, SearchIcon } from '@/shared/ui/icons'
import { Card, PageHeader, TableContainer } from '@/shared/ui/Layout'
import { tableClasses } from '@/shared/ui/table'
import { Pagination } from '@/shared/ui/Pagination'
import { EmptyState, ErrorState, LoadingList } from '@/shared/ui/States'
import { useStudentRates, useStudents } from '../api/students.queries'
import { StudentCreateDialog } from '../components/StudentCreateDialog'
import { StudentEditDialog } from '../components/StudentEditDialog'

const KEYS = ['q', 'classId', 'archived', 'page'] as const

function useCloseToList() {
  const navigate = useNavigate()
  const location = useLocation()
  return () => navigate({ pathname: '/students', search: location.search })
}

export function StudentCreateRoute() {
  const close = useCloseToList()
  const [params] = useSearchParamsState(KEYS)
  return <StudentCreateDialog defaultClassId={params.classId || undefined} onClose={close} />
}

export function StudentEditRoute() {
  const { studentId } = useParams()
  const close = useCloseToList()
  return studentId ? <StudentEditDialog studentId={studentId} onClose={close} /> : null
}

export default function StudentsPage() {
  useDocumentTitle('Alunos')
  const user = useCurrentUser()
  const location = useLocation()
  const [params, setParams] = useSearchParamsState(KEYS)
  const [search, setSearch] = useState(params.q)
  const page = Number(params.page) || 1

  const classes = useClassOptions()
  const year = useCurrentSchoolYear()
  const filters = {
    q: params.q || undefined,
    classId: params.classId || undefined,
    includeArchived: params.archived === '1' || undefined,
    page,
  }
  const students = useStudents(filters)
  const today = todayIso()
  const rates = useStudentRates(
    year.data
      ? { from: year.data.startsOn, to: today < year.data.endsOn ? today : year.data.endsOn }
      : null,
  )
  const classNames = new Map(
    classes.data?.map((c) => [c.id, `${c.name} · ${shiftLabels[c.shift]}`]),
  )

  function handleSearch(event: FormEvent) {
    event.preventDefault()
    setParams({ q: search.trim() })
  }

  const editLink = (student: Student) => ({
    pathname: `${student.id}/edit`,
    search: location.search,
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Alunos"
        actions={
          <Link to={{ pathname: 'new', search: location.search }} className={buttonVariants()}>
            <PlusIcon className="size-4" />
            Novo aluno
          </Link>
        }
      />

      <Card aria-label="Filtros de alunos">
        <form
          onSubmit={handleSearch}
          className="grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end"
        >
          <Field label="Buscar por nome ou matrícula">
            {(props) => (
              <Input
                {...props}
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
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
                    {classNames.get(c.id)}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Button type="submit" variant="secondary">
            <SearchIcon className="size-4" />
            Buscar
          </Button>
          {user.role === 'admin' && (
            <label className="flex min-h-11 items-center gap-2 text-sm text-fg sm:col-span-3">
              <input
                type="checkbox"
                className="size-5 accent-primary"
                checked={params.archived === '1'}
                onChange={(event) => setParams({ archived: event.target.checked ? '1' : null })}
              />
              Mostrar alunos arquivados
            </label>
          )}
        </form>
      </Card>

      <p role="status" aria-live="polite" className="text-sm text-fg-muted">
        {students.data && `${students.data.total} aluno(s) encontrado(s)`}
      </p>

      {students.isPending && <LoadingList label="Carregando alunos…" />}
      {students.isError && <ErrorState error={students.error} onRetry={() => students.refetch()} />}
      {students.data?.items.length === 0 && (
        <EmptyState
          title="Nenhum aluno encontrado"
          description={
            params.q || params.classId
              ? 'Tente mudar a busca ou a turma.'
              : 'Cadastre o primeiro aluno.'
          }
        />
      )}

      {students.data && students.data.items.length > 0 && (
        <>
          <div className="hidden lg:block">
            <TableContainer label="Lista de alunos">
              <table className={tableClasses.table}>
                <thead className={tableClasses.head}>
                  <tr>
                    <th scope="col" className={tableClasses.th}>
                      Nome
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      Matrícula
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      Turma
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      Nascimento
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      Frequência no ano
                    </th>
                    <th scope="col" className={tableClasses.th}>
                      <span className="sr-only">Ações</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {students.data.items.map((student) => (
                    <tr key={student.id} className={tableClasses.row}>
                      <td className={cn(tableClasses.td, 'font-medium')}>
                        {student.fullName}
                        {student.archivedAt && (
                          <Badge
                            tone="warning"
                            icon={<ArchiveIcon className="size-3.5" />}
                            className="ml-2"
                          >
                            Arquivado
                          </Badge>
                        )}
                      </td>
                      <td className={cn(tableClasses.td, 'tabular-nums')}>
                        {student.enrollmentNumber}
                      </td>
                      <td className={tableClasses.td}>
                        {student.currentClassId
                          ? (classNames.get(student.currentClassId) ?? '—')
                          : 'Sem turma'}
                      </td>
                      <td className={cn(tableClasses.td, 'tabular-nums')}>
                        {formatDate(student.birthDate)} ({calculateAge(student.birthDate)} anos)
                      </td>
                      <td className={tableClasses.td}>
                        <AttendanceRateBadge rate={rates.data?.get(student.id)} />
                      </td>
                      <td className={cn(tableClasses.td, 'text-right')}>
                        <Link
                          to={editLink(student)}
                          aria-label={`Editar ${student.fullName}`}
                          className={buttonVariants({ variant: 'ghost' })}
                        >
                          <PencilIcon className="size-4" />
                          Editar
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableContainer>
          </div>

          <ul className="flex flex-col gap-3 lg:hidden">
            {students.data.items.map((student) => (
              <li key={student.id} className="rounded-xl border border-line bg-surface p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-fg">{student.fullName}</p>
                    <p className="text-sm text-fg-muted tabular-nums">
                      Matrícula {student.enrollmentNumber} ·{' '}
                      {student.currentClassId
                        ? (classNames.get(student.currentClassId) ?? '—')
                        : 'Sem turma'}
                    </p>
                    <p className="text-sm text-fg-muted">{calculateAge(student.birthDate)} anos</p>
                  </div>
                  <AttendanceRateBadge rate={rates.data?.get(student.id)} />
                </div>
                <Link
                  to={editLink(student)}
                  aria-label={`Editar ${student.fullName}`}
                  className={cn(buttonVariants({ variant: 'secondary' }), 'mt-3 w-full')}
                >
                  <PencilIcon className="size-4" />
                  Editar
                </Link>
              </li>
            ))}
          </ul>

          <Pagination
            page={page}
            pageSize={students.data.pageSize}
            total={students.data.total}
            onPageChange={(next) => setParams({ page: String(next) }, { resetPage: false })}
          />
        </>
      )}

      <Outlet />
    </div>
  )
}
