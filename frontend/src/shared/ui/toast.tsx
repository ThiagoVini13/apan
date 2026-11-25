import { cn } from '@/shared/lib/cn'
import { Button } from './Button'
import { AlertIcon, CheckIcon, InfoIcon, XIcon } from './icons'
import { useToastStore, type Toast, type Tone } from './toast.store'

const toneClasses: Record<Tone, string> = {
  success: 'border-success text-success',
  error: 'border-danger text-danger',
  info: 'border-primary-text text-primary-text',
}

const icons: Record<Tone, typeof CheckIcon> = {
  success: CheckIcon,
  error: AlertIcon,
  info: InfoIcon,
}

export function Toaster() {
  const toasts = useToastStore((state) => state.toasts)
  const dismiss = useToastStore((state) => state.dismiss)
  const polite = toasts.filter((toast) => toast.tone !== 'error')
  const assertive = toasts.filter((toast) => toast.tone === 'error')

  const render = (items: Toast[]) =>
    items.map((toast) => {
      const Icon = icons[toast.tone]
      return (
        <div
          key={toast.id}
          className={cn(
            'pointer-events-auto flex items-start gap-3 rounded-xl border-2 bg-surface p-3 shadow-lg',
            toneClasses[toast.tone],
          )}
        >
          <Icon className="mt-0.5" />
          <p className="flex-1 text-sm font-medium text-fg">{toast.message}</p>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Fechar aviso"
            onClick={() => dismiss(toast.id)}
          >
            <XIcon />
          </Button>
        </div>
      )
    })

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-24 z-50 flex flex-col items-center gap-2 px-4 lg:bottom-6 lg:items-end">
      <div role="status" aria-live="polite" className="flex w-full max-w-sm flex-col gap-2">
        {render(polite)}
      </div>
      <div role="alert" aria-live="assertive" className="flex w-full max-w-sm flex-col gap-2">
        {render(assertive)}
      </div>
    </div>
  )
}
