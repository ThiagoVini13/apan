import { useState } from 'react'
import { useSchoolYears } from '@/shared/api/reference'
import type { SchoolYear } from '@/shared/api/types'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { cn } from '@/shared/lib/cn'
import { formatDate } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/Badge'
import { Button } from '@/shared/ui/Button'
import { ConfirmDialog } from '@/shared/ui/Dialog'
import { CalendarIcon, CheckIcon, PencilIcon, PlusIcon, TrashIcon } from '@/shared/ui/icons'
import { PageHeader, TableContainer } from '@/shared/ui/Layout'
import { tableClasses } from '@/shared/ui/table'
import { EmptyState, ErrorState, LoadingList } from '@/shared/ui/States'
import { notify } from '@/shared/ui/toast.store'
import { useDeleteSchoolYear } from '../api/school-years.queries'
import { CalendarDialog } from '../components/CalendarDialog'
import { SchoolYearDialog } from '../components/SchoolYearDialog'

export default function SchoolYearsPage() {
  useDocumentTitle('Anos letivos')
  const years = useSchoolYears()
  const remove = useDeleteSchoolYear()
  const [editing, setEditing] = useState<SchoolYear | null | 'new'>(null)
  const [calendar, setCalendar] = useState<SchoolYear | null>(null)
  const [deleting, setDeleting] = useState<SchoolYear | null>(null)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Anos letivos"
        description="Datas do ano, bimestres e calendário de feriados usados na chamada e nos relatórios."
        actions={
          <Button onClick={() => setEditing('new')}>
            <PlusIcon className="size-4" />
            Novo ano letivo
          </Button>
        }
      />
      {years.isPending && <LoadingList label="Carregando anos letivos…" />}
      {years.isError && <ErrorState error={years.error} onRetry={() => years.refetch()} />}
      {years.data?.length === 0 && <EmptyState title="Nenhum ano letivo cadastrado" />}
      {years.data && years.data.length > 0 && (
        <TableContainer label="Lista de anos letivos">
          <table className={tableClasses.table}>
            <thead className={tableClasses.head}>
              <tr>
                <th scope="col" className={tableClasses.th}>
                  Ano
                </th>
                <th scope="col" className={tableClasses.th}>
                  Período
                </th>
                <th scope="col" className={tableClasses.th}>
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {years.data.map((year) => (
                <tr key={year.id} className={tableClasses.row}>
                  <th scope="row" className={cn(tableClasses.td, 'font-medium')}>
                    {year.name}
                    {year.isCurrent && (
                      <Badge
                        tone="success"
                        icon={<CheckIcon className="size-3.5" />}
                        className="ml-2"
                      >
                        Atual
                      </Badge>
                    )}
                  </th>
                  <td className={cn(tableClasses.td, 'tabular-nums')}>
                    {formatDate(year.startsOn)} a {formatDate(year.endsOn)}
                  </td>
                  <td className={cn(tableClasses.td, 'whitespace-nowrap text-right')}>
                    <Button
                      variant="ghost"
                      aria-label={`Calendário de ${year.name}`}
                      onClick={() => setCalendar(year)}
                    >
                      <CalendarIcon className="size-4" />
                      Calendário
                    </Button>
                    <Button
                      variant="ghost"
                      aria-label={`Editar ${year.name}`}
                      onClick={() => setEditing(year)}
                    >
                      <PencilIcon className="size-4" />
                      Editar
                    </Button>
                    <Button
                      variant="ghost"
                      aria-label={`Excluir ${year.name}`}
                      onClick={() => setDeleting(year)}
                    >
                      <TrashIcon className="size-4" />
                      Excluir
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableContainer>
      )}
      {editing && (
        <SchoolYearDialog
          year={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}
      {calendar && <CalendarDialog year={calendar} onClose={() => setCalendar(null)} />}
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={`Excluir o ano letivo ${deleting?.name ?? ''}?`}
        description="Só é possível excluir anos letivos sem turmas cadastradas."
        confirmLabel="Excluir"
        tone="danger"
        isPending={remove.isPending}
        onConfirm={() =>
          deleting &&
          remove.mutate(deleting.id, {
            onSuccess: () => notify.success('Ano letivo excluído.'),
            onSettled: () => setDeleting(null),
          })
        }
      />
    </div>
  )
}
