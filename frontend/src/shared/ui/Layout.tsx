import type { ComponentPropsWithoutRef, ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'

type PageHeaderProps = { title: string; description?: string; actions?: ReactNode }

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-fg">{title}</h1>
        {description && <p className="mt-1 text-fg-muted">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}

export function Card({ className, ...props }: ComponentPropsWithoutRef<'section'>) {
  return (
    <section className={cn('rounded-xl border border-line bg-surface p-5', className)} {...props} />
  )
}

type StatProps = {
  label: string
  value: ReactNode
  hint?: ReactNode
  tone?: 'default' | 'danger' | 'success'
}

export function Stat({ label, value, hint, tone = 'default' }: StatProps) {
  return (
    <div className="rounded-xl border border-line bg-surface p-5">
      <p className="text-sm text-fg-muted">{label}</p>
      <p
        className={cn(
          'mt-1 text-3xl font-bold tabular-nums',
          tone === 'danger' ? 'text-danger' : tone === 'success' ? 'text-success' : 'text-fg',
        )}
      >
        {value}
      </p>
      {hint && <div className="mt-1 text-sm text-fg-muted">{hint}</div>}
    </div>
  )
}

type TableContainerProps = { label: string; children: ReactNode }

export function TableContainer({ label, children }: TableContainerProps) {
  return (
    <div
      role="region"
      aria-label={label}
      className="overflow-x-auto rounded-xl border border-line bg-surface"
      // Scrollable regions must be reachable by keyboard (WCAG 2.1.1).
      tabIndex={0}
    >
      {children}
    </div>
  )
}
