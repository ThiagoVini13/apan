import { Link, useNavigate } from 'react-router-dom'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { roleLabels } from '@/shared/lib/labels'
import { useCurrentUser, useEndSession } from '@/shared/session/session'
import { Button } from '@/shared/ui/Button'
import { buttonVariants } from '@/shared/ui/button-variants'
import { KeyIcon, LogOutIcon } from '@/shared/ui/icons'
import { Card, PageHeader } from '@/shared/ui/Layout'
import { ThemeToggle } from '../layouts/ThemeToggle'

export default function AccountPage() {
  useDocumentTitle('Minha conta')
  const user = useCurrentUser()
  const endSession = useEndSession()
  const navigate = useNavigate()

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Minha conta" />
      <Card className="flex max-w-lg flex-col gap-5">
        <dl className="grid gap-2">
          <div>
            <dt className="text-sm text-fg-muted">Nome</dt>
            <dd className="font-medium text-fg">{user.fullName}</dd>
          </div>
          <div>
            <dt className="text-sm text-fg-muted">E-mail</dt>
            <dd className="font-medium text-fg">{user.email}</dd>
          </div>
          <div>
            <dt className="text-sm text-fg-muted">Perfil</dt>
            <dd className="font-medium text-fg">{roleLabels[user.role]}</dd>
          </div>
        </dl>
        <ThemeToggle />
        <div className="flex flex-wrap gap-2">
          <Link to="/change-password" className={buttonVariants({ variant: 'secondary' })}>
            <KeyIcon className="size-4" />
            Alterar senha
          </Link>
          <Button
            variant="secondary"
            onClick={async () => {
              await endSession()
              navigate('/login', { replace: true })
            }}
          >
            <LogOutIcon className="size-4" />
            Sair
          </Button>
        </div>
      </Card>
    </div>
  )
}
