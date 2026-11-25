import { Link } from 'react-router-dom'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { PageHeader } from '@/shared/ui/Layout'
import { adminNav } from '../layouts/navigation'

export default function AdminHomePage() {
  useDocumentTitle('Administração')
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Administração" />
      <ul className="grid gap-3 sm:grid-cols-2">
        {adminNav.map(({ to, label, icon: Icon }) => (
          <li key={to}>
            <Link
              to={to}
              className="flex min-h-16 items-center gap-3 rounded-xl border border-line bg-surface px-4 font-semibold text-fg hover:bg-surface-muted"
            >
              <Icon className="text-primary-text" />
              {label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
