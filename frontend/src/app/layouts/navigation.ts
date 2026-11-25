import type { Role } from '@/shared/api/types'
import {
  BookIcon,
  CalendarIcon,
  ChartIcon,
  ClipboardIcon,
  HistoryIcon,
  HomeIcon,
  SchoolIcon,
  SettingsIcon,
  UsersIcon,
} from '@/shared/ui/icons'

export type NavItem = {
  to: string
  label: string
  icon: typeof HomeIcon
  end?: boolean
  roles?: Role[]
}

export const mainNav: NavItem[] = [
  { to: '/', label: 'Início', icon: HomeIcon, end: true },
  { to: '/roll-call', label: 'Chamada', icon: ClipboardIcon },
  { to: '/students', label: 'Alunos', icon: UsersIcon },
  { to: '/reports', label: 'Relatórios', icon: ChartIcon },
]

export const adminNav: NavItem[] = [
  { to: '/admin/users', label: 'Usuários', icon: UsersIcon, roles: ['admin'] },
  { to: '/admin/classes', label: 'Turmas', icon: SchoolIcon, roles: ['admin'] },
  { to: '/admin/subjects', label: 'Disciplinas', icon: BookIcon, roles: ['admin'] },
  { to: '/admin/school-years', label: 'Anos letivos', icon: CalendarIcon, roles: ['admin'] },
  { to: '/admin/audit', label: 'Auditoria', icon: HistoryIcon, roles: ['admin'] },
]

export const adminHomeItem: NavItem = {
  to: '/admin',
  label: 'Admin',
  icon: SettingsIcon,
  roles: ['admin'],
}
