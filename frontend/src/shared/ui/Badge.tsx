import { cva, type VariantProps } from 'class-variance-authority'
import type { ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'
import { MIN_ATTENDANCE_RATE } from '@/shared/lib/constants'
import { formatPercent } from '@/shared/lib/format'
import { AlertIcon, CheckIcon, InfoIcon } from './icons'

const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold',
  {
    variants: {
      tone: {
        neutral: 'border-line-strong bg-surface-muted text-fg',
        success: 'border-success bg-success-bg text-success',
        danger: 'border-danger bg-danger-bg text-danger',
        warning: 'border-warning bg-warning-bg text-warning',
        info: 'border-primary-text bg-primary-bg text-primary-text',
      },
    },
    defaultVariants: { tone: 'neutral' },
  },
)

type BadgeProps = VariantProps<typeof badgeVariants> & {
  children: ReactNode
  icon?: ReactNode
  className?: string
}

export function Badge({ tone, icon, children, className }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ tone }), className)}>
      {icon}
      {children}
    </span>
  )
}

export function AttendanceRateBadge({ rate }: { rate: number | null | undefined }) {
  if (rate === null || rate === undefined) {
    return (
      <Badge tone="neutral" icon={<InfoIcon className="size-3.5" />}>
        Sem aulas
      </Badge>
    )
  }
  const atRisk = rate < MIN_ATTENDANCE_RATE
  return (
    <Badge
      tone={atRisk ? 'danger' : 'success'}
      icon={atRisk ? <AlertIcon className="size-3.5" /> : <CheckIcon className="size-3.5" />}
    >
      <span className="tabular-nums">{formatPercent(rate)}</span>
      <span className="sr-only">{atRisk ? ', abaixo do mínimo de 75%' : ', regular'}</span>
    </Badge>
  )
}
