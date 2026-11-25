import { Link, isRouteErrorResponse, useRouteError } from 'react-router-dom'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { buttonVariants } from '@/shared/ui/button-variants'
import { AlertIcon } from '@/shared/ui/icons'

function ErrorLayout({ title, description }: { title: string; description: string }) {
  useDocumentTitle(title)
  return (
    <main
      id="main"
      className="mx-auto flex max-w-lg flex-col items-center gap-3 px-4 py-16 text-center"
    >
      <AlertIcon className="size-10 text-fg-muted" />
      <h1 className="text-2xl font-bold text-fg">{title}</h1>
      <p className="text-fg-muted">{description}</p>
      <Link to="/" className={buttonVariants({ variant: 'secondary' })}>
        Voltar para o início
      </Link>
    </main>
  )
}

export function NotFoundPage() {
  return (
    <ErrorLayout
      title="Página não encontrada"
      description="O endereço não existe ou foi alterado."
    />
  )
}

export function RouteErrorPage() {
  const error = useRouteError()
  if (isRouteErrorResponse(error) && error.status === 404) return <NotFoundPage />
  return (
    <ErrorLayout
      title="Algo deu errado"
      description="Ocorreu um erro inesperado nesta tela. Recarregue a página; se o problema continuar, avise a coordenação."
    />
  )
}
