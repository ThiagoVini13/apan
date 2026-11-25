import type { ReactNode } from 'react'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'

type AuthLayoutProps = { title: string; description?: string; children: ReactNode }

export function AuthLayout({ title, description, children }: AuthLayoutProps) {
  useDocumentTitle(title)
  return (
    <main id="main" className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md rounded-2xl border border-line bg-surface p-6 shadow-sm sm:p-8">
        <p className="text-sm font-semibold text-primary-text">APAN Frequência</p>
        <h1 className="mt-1 text-2xl font-bold text-fg">{title}</h1>
        {description && <p className="mt-2 text-fg-muted">{description}</p>}
        <div className="mt-6">{children}</div>
      </div>
    </main>
  )
}
