import type { ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'
import { errorMessage } from '@/shared/lib/errors'
import { Button } from './Button'
import { AlertIcon, InfoIcon } from './icons'

type EmptyStateProps = { title: string; description?: string; action?: ReactNode }

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-line-strong bg-surface px-6 py-10 text-center">
      <InfoIcon className="size-7 text-fg-muted" />
      <p className="font-semibold text-fg">{title}</p>
      {description && <p className="max-w-md text-sm text-fg-muted">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

type ErrorStateProps = { error: unknown; onRetry?: () => void; title?: string }

export function ErrorState({
  error,
  onRetry,
  title = 'Não foi possível carregar',
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-2 rounded-xl border border-danger bg-danger-bg px-6 py-8 text-center"
    >
      <AlertIcon className="size-7 text-danger" />
      <p className="font-semibold text-fg">{title}</p>
      <p className="max-w-md text-sm text-fg">{errorMessage(error)}</p>
      {onRetry && (
        <Button variant="secondary" className="mt-2" onClick={onRetry}>
          Tentar novamente
        </Button>
      )}
    </div>
  )
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn('animate-pulse rounded-lg bg-line', className)} />
}

export function LoadingList({ label, rows = 4 }: { label: string; rows?: number }) {
  return (
    <div aria-busy="true" aria-live="polite" className="flex flex-col gap-3">
      <span className="sr-only">{label}</span>
      {Array.from({ length: rows }, (_, index) => (
        <Skeleton key={index} className="h-14 w-full" />
      ))}
    </div>
  )
}
