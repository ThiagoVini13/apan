import { useState } from 'react'
import { useClassOptions, useCurrentSchoolYear, useSchoolYears } from '@/shared/api/reference'
import type { SchoolClass } from '@/shared/api/types'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { useSearchParamsState } from '@/shared/hooks/useSearchParamsState'
import { cn } from '@/shared/lib/cn'
import { shiftLabels } from '@/shared/lib/labels'
import { Badge } from '@/shared/ui/Badge'
import { Button } from '@/shared/ui/Button'
import { ConfirmDialog } from '@/shared/ui/Dialog'
import { Field, Select } from '@/shared/ui/Field'
import { ArchiveIcon, PencilIcon, PlusIcon, UsersIcon } from '@/shared/ui/icons'
import { Card, PageHeader, TableContainer } from '@/shared/ui/Layout'
import { tableClasses } from '@/shared/ui/table'
import { EmptyState, ErrorState, LoadingList } from '@/shared/ui/States'
import { notify } from '@/shared/ui/toast.store'
import { useArchiveClass } from '../api/classes.queries'
import { ClassFormDialog } from '../components/ClassFormDialog'
import { SubjectTeachersDialog } from '../components/SubjectTeachersDialog'

const KEYS = ['yearId', 'archived'] as const

export default function ClassesPage() {
  useDocumentTitle('Turmas')
  const [params, setParams] = useSearchParamsState(KEYS)
  const years = useSchoolYears()
  const currentYear = useCurrentSchoolYear()
  const yearId = params.yearId || currentYear.data?.id || ''
  const showArchived = params.archived === '1'
  const classes = useClassOptions({
    schoolYearId: yearId || undefined,
    isActive: showArchived ? undefined : true,
  })
  const archive = useArchiveClass()
  const [editing, setEditing] = useState<SchoolClass | null | 'new'>(null)
  const [assigning, setAssigning] = useState<SchoolClass | null>(null)
  const [archiving, setArchiving] = useState<SchoolClass | null>(null)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Turmas"
        actions={
          <Button onClick={() => setEditing('new')}>
            <PlusIcon className="size-4" />
            Nova turma
          </Button>
        }
      />

      <Card aria-label="Filtros de turmas">
        <div className="grid gap-4 sm:grid-cols-2 sm:items-end">
          <Field label="Ano letivo">
            {(props) => (
              <Select
                {...props}
                value={yearId}
                onChange={(event) => setParams({ yearId: event.target.value })}
              >
                {years.data?.map((year) => (
                  <option key={year.id} value={year.id}>
                    {year.name}
                    {year.isCurrent ? ' (atual)' : ''}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <label className="flex min-h-11 items-center gap-2 text-sm text-fg">
            <input
              type="checkbox"
              className="size-5 accent-primary"
              checked={showArchived}
              onChange={(event) => setParams({ archived: event.target.checked ? '1' : null })}
            />
            Mostrar turmas arquivadas
          </label>
        </div>
      </Card>

      {years.data?.length === 0 && (
        <EmptyState
          title="Nenhum ano letivo cadastrado"
          description="Cadastre o ano letivo antes das turmas."
        />
      )}
      {classes.isPending && <LoadingList label="Carregando turmas…" />}
      {classes.isError && <ErrorState error={classes.error} onRetry={() => classes.refetch()} />}
      {classes.data?.length === 0 && <EmptyState title="Nenhuma turma neste ano letivo" />}
      {classes.data && classes.data.length > 0 && (
        <TableContainer label="Lista de turmas">
          <table className={tableClasses.table}>
            <thead className={tableClasses.head}>
              <tr>
                <th scope="col" className={tableClasses.th}>
                  Turma
                </th>
                <th scope="col" className={tableClasses.th}>
                  Turno
                </th>
                <th scope="col" className={tableClasses.th}>
                  Sala
                </th>
                <th scope="col" className={tableClasses.th}>
                  Alunos
                </th>
                <th scope="col" className={tableClasses.th}>
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {classes.data.map((schoolClass) => (
                <tr key={schoolClass.id} className={tableClasses.row}>
                  <th scope="row" className={cn(tableClasses.td, 'font-medium')}>
                    {schoolClass.name}
                    {!schoolClass.isActive && (
                      <Badge
                        tone="warning"
                        icon={<ArchiveIcon className="size-3.5" />}
                        className="ml-2"
                      >
                        Arquivada
                      </Badge>
                    )}
                  </th>
                  <td className={tableClasses.td}>{shiftLabels[schoolClass.shift]}</td>
                  <td className={tableClasses.td}>{schoolClass.room ?? '—'}</td>
                  <td className={cn(tableClasses.td, 'tabular-nums')}>
                    {schoolClass.studentCount}
                    {schoolClass.capacity ? ` de ${schoolClass.capacity}` : ''}
                  </td>
                  <td className={cn(tableClasses.td, 'whitespace-nowrap text-right')}>
                    <Button
                      variant="ghost"
                      aria-label={`Professores de ${schoolClass.name}`}
                      onClick={() => setAssigning(schoolClass)}
                    >
                      <UsersIcon className="size-4" />
                      Professores
                    </Button>
                    <Button
                      variant="ghost"
                      aria-label={`Editar ${schoolClass.name}`}
                      onClick={() => setEditing(schoolClass)}
                    >
                      <PencilIcon className="size-4" />
                      Editar
                    </Button>
                    {schoolClass.isActive && (
                      <Button
                        variant="ghost"
                        aria-label={`Arquivar ${schoolClass.name}`}
                        onClick={() => setArchiving(schoolClass)}
                      >
                        <ArchiveIcon className="size-4" />
                        Arquivar
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableContainer>
      )}

      {editing && (
        <ClassFormDialog
          schoolClass={editing === 'new' ? null : editing}
          defaultYearId={yearId}
          onClose={() => setEditing(null)}
        />
      )}
      {assigning && (
        <SubjectTeachersDialog schoolClass={assigning} onClose={() => setAssigning(null)} />
      )}
      <ConfirmDialog
        open={archiving !== null}
        onOpenChange={(open) => !open && setArchiving(null)}
        title={`Arquivar ${archiving?.name ?? ''}?`}
        description="A turma deixa de receber matrículas e chamadas. O histórico continua nos relatórios."
        confirmLabel="Arquivar"
        tone="danger"
        isPending={archive.isPending}
        onConfirm={() =>
          archiving &&
          archive.mutate(archiving.id, {
            onSuccess: () => notify.success('Turma arquivada.'),
            onSettled: () => setArchiving(null),
          })
        }
      />
    </div>
  )
}
