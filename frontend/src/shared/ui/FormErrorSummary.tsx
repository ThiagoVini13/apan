import { AlertIcon } from './icons'

export function FormErrorSummary({ message }: { message: string | null | undefined }) {
  if (!message) return null
  return (
    <div
      role="alert"
      className="flex items-start gap-2 rounded-lg border border-danger bg-danger-bg p-3 text-sm text-fg"
    >
      <AlertIcon className="mt-0.5 size-4 text-danger" />
      <span>{message}</span>
    </div>
  )
}
