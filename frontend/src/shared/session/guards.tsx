import type { ReactNode } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import type { Role } from '@/shared/api/types'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { ShieldIcon } from '@/shared/ui/icons'
import { Skeleton } from '@/shared/ui/States'
import { useSession } from './session'

const PASSWORD_CHANGE_PATH = '/change-password'

export function RequireAuth() {
  const { data: user, isPending } = useSession()
  const location = useLocation()

  if (isPending) {
    return (
      <div aria-busy="true" className="mx-auto flex max-w-3xl flex-col gap-4 p-6">
        <span className="sr-only">Carregando sua sessão…</span>
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }
  if (!user) {
    const next = `${location.pathname}${location.search}`
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />
  }
  if (user.mustChangePassword && location.pathname !== PASSWORD_CHANGE_PATH) {
    return <Navigate to={PASSWORD_CHANGE_PATH} replace />
  }
  return <Outlet />
}

export function Forbidden() {
  useDocumentTitle('Sem permissão')
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center gap-3 py-16 text-center">
      <ShieldIcon className="size-10 text-fg-muted" />
      <h1 className="text-2xl font-bold text-fg">Sem permissão</h1>
      <p className="text-fg-muted">
        Esta área é restrita à administração. Se precisar de acesso, fale com a coordenação.
      </p>
    </div>
  )
}

type RequireRoleProps = { roles: Role[]; children?: ReactNode }

export function RequireRole({ roles, children }: RequireRoleProps) {
  const { data: user } = useSession()
  if (!user || !roles.includes(user.role)) return <Forbidden />
  return children ?? <Outlet />
}
