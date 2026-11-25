import { useState } from 'react'
import type { Role, User } from '@/shared/api/types'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { useSearchParamsState } from '@/shared/hooks/useSearchParamsState'
import { cn } from '@/shared/lib/cn'
import { formatDateTime } from '@/shared/lib/format'
import { optionsFrom, roleLabels } from '@/shared/lib/labels'
import { useCurrentUser } from '@/shared/session/session'
import { Badge } from '@/shared/ui/Badge'
import { Button } from '@/shared/ui/Button'
import { ConfirmDialog } from '@/shared/ui/Dialog'
import { Field, Input, Select } from '@/shared/ui/Field'
import { CheckIcon, PencilIcon, PlusIcon, XIcon } from '@/shared/ui/icons'
import { Card, PageHeader, TableContainer } from '@/shared/ui/Layout'
import { tableClasses } from '@/shared/ui/table'
import { Pagination } from '@/shared/ui/Pagination'
import { EmptyState, ErrorState, LoadingList } from '@/shared/ui/States'
import { notify } from '@/shared/ui/toast.store'
import { useSetUserActive, useUsers } from '../api/users.queries'
import { UserFormDialog } from '../components/UserFormDialog'

const KEYS = ['q', 'role', 'status', 'page'] as const

export default function UsersPage() {
  useDocumentTitle('Usuários')
  const me = useCurrentUser()
  const [params, setParams] = useSearchParamsState(KEYS)
  const [editing, setEditing] = useState<User | null | 'new'>(null)
  const [toggling, setToggling] = useState<User | null>(null)
  const setActive = useSetUserActive()
  const page = Number(params.page) || 1
  const users = useUsers({
    q: params.q || undefined,
    role: (params.role as Role) || undefined,
    isActive: params.status ? params.status === 'active' : undefined,
    page,
  })

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Usuários"
        description="Contas de administração e de professores."
        actions={
          <Button onClick={() => setEditing('new')}>
            <PlusIcon className="size-4" />
            Convidar usuário
          </Button>
        }
      />

      <Card aria-label="Filtros de usuários">
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Buscar por nome ou e-mail">
            {(props) => (
              <Input
                {...props}
                type="search"
                defaultValue={params.q}
                onBlur={(event) => setParams({ q: event.target.value.trim() })}
              />
            )}
          </Field>
          <Field label="Perfil">
            {(props) => (
              <Select
                {...props}
                value={params.role}
                onChange={(event) => setParams({ role: event.target.value })}
              >
                <option value="">Todos</option>
                {optionsFrom(roleLabels).map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Situação">
            {(props) => (
              <Select
                {...props}
                value={params.status}
                onChange={(event) => setParams({ status: event.target.value })}
              >
                <option value="">Todas</option>
                <option value="active">Ativas</option>
                <option value="inactive">Desativadas</option>
              </Select>
            )}
          </Field>
        </div>
      </Card>

      {users.isPending && <LoadingList label="Carregando usuários…" />}
      {users.isError && <ErrorState error={users.error} onRetry={() => users.refetch()} />}
      {users.data?.items.length === 0 && <EmptyState title="Nenhum usuário encontrado" />}
      {users.data && users.data.items.length > 0 && (
        <>
          <TableContainer label="Lista de usuários">
            <table className={tableClasses.table}>
              <thead className={tableClasses.head}>
                <tr>
                  <th scope="col" className={tableClasses.th}>
                    Nome
                  </th>
                  <th scope="col" className={tableClasses.th}>
                    E-mail
                  </th>
                  <th scope="col" className={tableClasses.th}>
                    Perfil
                  </th>
                  <th scope="col" className={tableClasses.th}>
                    Situação
                  </th>
                  <th scope="col" className={tableClasses.th}>
                    Último acesso
                  </th>
                  <th scope="col" className={tableClasses.th}>
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {users.data.items.map((user) => (
                  <tr key={user.id} className={tableClasses.row}>
                    <th scope="row" className={cn(tableClasses.td, 'font-medium')}>
                      {user.fullName}
                    </th>
                    <td className={tableClasses.td}>{user.email}</td>
                    <td className={tableClasses.td}>{roleLabels[user.role]}</td>
                    <td className={tableClasses.td}>
                      {!user.isActive ? (
                        <Badge tone="neutral" icon={<XIcon className="size-3.5" />}>
                          Desativada
                        </Badge>
                      ) : user.mustChangePassword ? (
                        <Badge tone="warning">Convite pendente</Badge>
                      ) : (
                        <Badge tone="success" icon={<CheckIcon className="size-3.5" />}>
                          Ativa
                        </Badge>
                      )}
                    </td>
                    <td className={cn(tableClasses.td, 'tabular-nums')}>
                      {user.lastLoginAt ? formatDateTime(user.lastLoginAt) : '—'}
                    </td>
                    <td className={cn(tableClasses.td, 'whitespace-nowrap text-right')}>
                      <Button
                        variant="ghost"
                        aria-label={`Editar ${user.fullName}`}
                        onClick={() => setEditing(user)}
                      >
                        <PencilIcon className="size-4" />
                        Editar
                      </Button>
                      {user.id !== me.id && (
                        <Button
                          variant="ghost"
                          aria-label={`${user.isActive ? 'Desativar' : 'Reativar'} ${user.fullName}`}
                          onClick={() => setToggling(user)}
                        >
                          {user.isActive ? 'Desativar' : 'Reativar'}
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableContainer>
          <Pagination
            page={page}
            pageSize={users.data.pageSize}
            total={users.data.total}
            onPageChange={(next) => setParams({ page: String(next) }, { resetPage: false })}
          />
        </>
      )}

      {editing && (
        <UserFormDialog
          user={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}
      <ConfirmDialog
        open={toggling !== null}
        onOpenChange={(open) => !open && setToggling(null)}
        title={
          toggling?.isActive
            ? `Desativar ${toggling.fullName}?`
            : `Reativar ${toggling?.fullName ?? ''}?`
        }
        description={
          toggling?.isActive
            ? 'A pessoa perde o acesso imediatamente. O histórico de chamadas é mantido.'
            : 'A pessoa volta a acessar o sistema com a mesma senha.'
        }
        confirmLabel={toggling?.isActive ? 'Desativar' : 'Reativar'}
        tone={toggling?.isActive ? 'danger' : 'primary'}
        isPending={setActive.isPending}
        onConfirm={() =>
          toggling &&
          setActive.mutate(
            { id: toggling.id, active: !toggling.isActive },
            {
              onSuccess: () =>
                notify.success(toggling.isActive ? 'Conta desativada.' : 'Conta reativada.'),
              onSettled: () => setToggling(null),
            },
          )
        }
      />
    </div>
  )
}
