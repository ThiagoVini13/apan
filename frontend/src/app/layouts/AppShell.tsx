import { useEffect, useRef } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { cn } from '@/shared/lib/cn'
import { roleLabels } from '@/shared/lib/labels'
import { useCurrentUser, useEndSession } from '@/shared/session/session'
import { Button } from '@/shared/ui/Button'
import { KeyIcon, LogOutIcon } from '@/shared/ui/icons'
import { adminHomeItem, adminNav, mainNav, type NavItem } from './navigation'
import { ThemeToggle } from './ThemeToggle'

function SidebarLink({ item }: { item: NavItem }) {
  const Icon = item.icon
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        cn(
          'flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium',
          isActive ? 'bg-primary-bg text-primary-text' : 'text-fg hover:bg-surface-muted',
        )
      }
    >
      <Icon />
      {item.label}
    </NavLink>
  )
}

function BottomLink({ item }: { item: NavItem }) {
  const Icon = item.icon
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        cn(
          'flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 text-xs font-medium',
          isActive ? 'text-primary-text' : 'text-fg-muted',
        )
      }
    >
      <Icon />
      {item.label}
    </NavLink>
  )
}

function useFocusOnNavigation() {
  const location = useLocation()
  const mainRef = useRef<HTMLElement>(null)
  const isFirst = useRef(true)

  useEffect(() => {
    if (isFirst.current) {
      isFirst.current = false
      return
    }
    const heading = mainRef.current?.querySelector<HTMLElement>('h1')
    const target = heading ?? mainRef.current
    if (!target) return
    if (heading) heading.tabIndex = -1
    target.focus({ preventScroll: false })
  }, [location.pathname])

  return mainRef
}

export function AppShell() {
  const user = useCurrentUser()
  const endSession = useEndSession()
  const navigate = useNavigate()
  const mainRef = useFocusOnNavigation()
  const isAdmin = user.role === 'admin'

  async function handleLogout() {
    await endSession()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen lg:flex">
      <a
        href="#main"
        className="sr-only z-50 rounded-lg bg-primary px-4 py-3 font-semibold text-primary-fg focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
      >
        Pular para o conteúdo
      </a>

      <aside className="hidden border-r border-line bg-surface lg:flex lg:w-64 lg:flex-col">
        <div className="flex h-16 items-center gap-2 border-b border-line px-5">
          <span className="text-lg font-bold text-fg">APAN</span>
          <span className="text-sm text-fg-muted">Frequência</span>
        </div>
        <nav aria-label="Principal" className="flex flex-1 flex-col gap-1 overflow-y-auto p-3">
          {mainNav.map((item) => (
            <SidebarLink key={item.to} item={item} />
          ))}
          {isAdmin && (
            <>
              <p className="mt-4 mb-1 px-3 text-xs font-semibold tracking-wide text-fg-muted uppercase">
                Administração
              </p>
              {adminNav.map((item) => (
                <SidebarLink key={item.to} item={item} />
              ))}
            </>
          )}
        </nav>
        <div className="flex flex-col gap-3 border-t border-line p-4">
          <div>
            <p className="font-semibold text-fg">{user.fullName}</p>
            <p className="text-sm text-fg-muted">{roleLabels[user.role]}</p>
          </div>
          <ThemeToggle />
          <Link
            to="/change-password"
            className="flex min-h-11 items-center gap-2 rounded-lg px-2 text-sm font-medium text-primary-text hover:bg-surface-muted"
          >
            <KeyIcon className="size-4" />
            Alterar senha
          </Link>
          <Button variant="secondary" onClick={handleLogout}>
            <LogOutIcon className="size-4" />
            Sair
          </Button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between gap-3 border-b border-line bg-surface px-4 lg:hidden">
          <span className="font-bold text-fg">APAN Frequência</span>
          <div className="flex items-center gap-1">
            <Link
              to="/account"
              className="flex min-h-11 items-center rounded-lg px-3 text-sm font-medium text-primary-text"
            >
              {user.fullName.split(' ')[0]}
            </Link>
            <Button variant="ghost" size="icon" aria-label="Sair" onClick={handleLogout}>
              <LogOutIcon />
            </Button>
          </div>
        </header>

        <main
          id="main"
          ref={mainRef}
          tabIndex={-1}
          className="mx-auto w-full max-w-6xl flex-1 px-4 pt-6 pb-28 focus:outline-none lg:px-8 lg:pb-10"
        >
          <Outlet />
        </main>
      </div>

      <nav
        aria-label="Principal (celular)"
        className="fixed inset-x-0 bottom-0 z-30 flex border-t border-line bg-surface lg:hidden"
      >
        {mainNav.map((item) => (
          <BottomLink key={item.to} item={item} />
        ))}
        {isAdmin && <BottomLink item={adminHomeItem} />}
      </nav>
    </div>
  )
}
