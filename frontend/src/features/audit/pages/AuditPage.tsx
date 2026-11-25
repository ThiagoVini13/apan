import type { AuditLog } from '@/shared/api/types'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { useSearchParamsState } from '@/shared/hooks/useSearchParamsState'
import { cn } from '@/shared/lib/cn'
import { formatDateTime } from '@/shared/lib/format'
import { Field, Input, Select } from '@/shared/ui/Field'
import { Card, PageHeader, TableContainer } from '@/shared/ui/Layout'
import { tableClasses } from '@/shared/ui/table'
import { Pagination } from '@/shared/ui/Pagination'
import { EmptyState, ErrorState, LoadingList } from '@/shared/ui/States'
import { useAuditLogs } from '../api/audit.queries'
import { actionGroups, describeAction } from '../labels'

const KEYS = ['action', 'from', 'to', 'page'] as const

function detailsText(entry: AuditLog): string {
  const parts = Object.entries(entry.details)
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : String(value)}`)
  return parts.join(' · ')
}

export default function AuditPage() {
  useDocumentTitle('Auditoria')
  const [params, setParams] = useSearchParamsState(KEYS)
  const page = Number(params.page) || 1
  const logs = useAuditLogs({
    action: params.action || undefined,
    from: params.from || undefined,
    to: params.to || undefined,
    page,
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Auditoria"
        description="Registro de acessos e alterações. Os registros não podem ser editados nem apagados."
      />
      <Card aria-label="Filtros da auditoria">
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Tipo de evento">
            {(props) => (
              <Select
                {...props}
                value={params.action}
                onChange={(event) => setParams({ action: event.target.value })}
              >
                <option value="">Todos</option>
                {actionGroups.map((group) => (
                  <option key={group.prefix} value={group.prefix}>
                    {group.label}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="De">
            {(props) => (
              <Input
                {...props}
                type="date"
                value={params.from}
                onChange={(event) => setParams({ from: event.target.value })}
              />
            )}
          </Field>
          <Field label="Até">
            {(props) => (
              <Input
                {...props}
                type="date"
                value={params.to}
                onChange={(event) => setParams({ to: event.target.value })}
              />
            )}
          </Field>
        </div>
      </Card>

      {logs.isPending && <LoadingList label="Carregando registros…" />}
      {logs.isError && <ErrorState error={logs.error} onRetry={() => logs.refetch()} />}
      {logs.data?.items.length === 0 && <EmptyState title="Nenhum registro encontrado" />}
      {logs.data && logs.data.items.length > 0 && (
        <>
          <TableContainer label="Registros de auditoria">
            <table className={tableClasses.table}>
              <thead className={tableClasses.head}>
                <tr>
                  <th scope="col" className={tableClasses.th}>
                    Quando
                  </th>
                  <th scope="col" className={tableClasses.th}>
                    Quem
                  </th>
                  <th scope="col" className={tableClasses.th}>
                    Evento
                  </th>
                  <th scope="col" className={tableClasses.th}>
                    Detalhes
                  </th>
                  <th scope="col" className={tableClasses.th}>
                    IP
                  </th>
                </tr>
              </thead>
              <tbody>
                {logs.data.items.map((entry) => (
                  <tr key={entry.id} className={tableClasses.row}>
                    <td className={cn(tableClasses.td, 'whitespace-nowrap tabular-nums')}>
                      {formatDateTime(entry.createdAt)}
                    </td>
                    <td className={tableClasses.td}>{entry.actorName ?? 'Sistema'}</td>
                    <td className={tableClasses.td}>{describeAction(entry.action)}</td>
                    <td className={cn(tableClasses.td, 'text-fg-muted')}>
                      {detailsText(entry) || '—'}
                    </td>
                    <td className={cn(tableClasses.td, 'tabular-nums')}>{entry.ip ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableContainer>
          <Pagination
            page={page}
            pageSize={logs.data.pageSize}
            total={logs.data.total}
            onPageChange={(next) => setParams({ page: String(next) }, { resetPage: false })}
          />
        </>
      )}
    </div>
  )
}
