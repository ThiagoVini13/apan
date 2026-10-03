import { NavLink, Outlet } from 'react-router-dom'

const navLinks = [
  { to: '/',          label: 'Início',    icon: '🏠' },
  { to: '/roll-call', label: 'Chamada',   icon: '📋' },
  { to: '/students',  label: 'Alunos',    icon: '👥' },
  { to: '/reports',   label: 'Relatórios',icon: '📊' },
]

function NavItem({ to, label, icon, end }: { to: string; label: string; icon: string; end?: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
          isActive
            ? 'bg-slate-700 text-white'
            : 'text-slate-300 hover:bg-slate-700/50 hover:text-white'
        }`
      }
    >
      <span>{icon}</span>
      <span>{label}</span>
    </NavLink>
  )
}

function MobileNavItem({ to, label, icon, end }: { to: string; label: string; icon: string; end?: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `flex flex-col items-center gap-1 px-3 py-2 text-xs font-medium transition-colors ${
          isActive ? 'text-blue-600' : 'text-slate-500 hover:text-slate-700'
        }`
      }
    >
      <span className="text-xl">{icon}</span>
      <span>{label}</span>
    </NavLink>
  )
}

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar - desktop */}
      <aside className="hidden lg:flex lg:w-56 lg:flex-col bg-slate-900">
        <div className="flex h-16 items-center px-4 border-b border-slate-700">
          <span className="text-white font-bold text-xl">APAN</span>
        </div>
        <nav className="flex flex-col gap-1 p-3 flex-1">
          {navLinks.map((link) => (
            <NavItem key={link.to} {...link} end={link.to === '/'} />
          ))}
        </nav>
        <div className="p-4 border-t border-slate-700">
          <p className="text-slate-400 text-xs">Sistema de Frequência Escolar</p>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Top header - mobile logo */}
        <header className="flex lg:hidden h-14 items-center px-4 bg-slate-900 text-white font-bold text-lg">
          APAN
        </header>

        <main className="flex-1 p-4 lg:p-8 pb-20 lg:pb-8">
          <Outlet />
        </main>
      </div>

      {/* Bottom navigation - mobile */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 flex justify-around bg-white border-t border-slate-200 z-10">
        {navLinks.map((link) => (
          <MobileNavItem key={link.to} {...link} end={link.to === '/'} />
        ))}
      </nav>
    </div>
  )
}
