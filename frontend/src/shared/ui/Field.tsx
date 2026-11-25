import { forwardRef, useId, type ComponentPropsWithoutRef, type ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'
import { AlertIcon } from './icons'

export type FieldControlProps = {
  id: string
  'aria-invalid': boolean | undefined
  'aria-describedby': string | undefined
  'aria-required': boolean | undefined
}

type FieldProps = {
  label: string
  error?: string
  hint?: string
  required?: boolean
  className?: string
  children: (props: FieldControlProps) => ReactNode
}

export function Field({ label, error, hint, required, className, children }: FieldProps) {
  const id = useId()
  const hintId = `${id}-hint`
  const errorId = `${id}-error`
  const describedBy = [hint ? hintId : null, error ? errorId : null].filter(Boolean).join(' ')

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <label htmlFor={id} className="text-sm font-medium text-fg">
        {label}
        {required && (
          <span className="text-danger" aria-hidden="true">
            {' '}
            *
          </span>
        )}
      </label>
      {children({
        id,
        'aria-invalid': error ? true : undefined,
        'aria-describedby': describedBy || undefined,
        'aria-required': required || undefined,
      })}
      {hint && (
        <p id={hintId} className="text-sm text-fg-muted">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className="flex items-start gap-1.5 text-sm font-medium text-danger">
          <AlertIcon className="mt-0.5 size-4" />
          <span>{error}</span>
        </p>
      )}
    </div>
  )
}

const controlClasses =
  'w-full min-h-11 rounded-lg border border-line-strong bg-surface px-3 text-base text-fg placeholder:text-fg-muted aria-[invalid=true]:border-danger aria-[invalid=true]:border-2 disabled:opacity-60'

export const Input = forwardRef<HTMLInputElement, ComponentPropsWithoutRef<'input'>>(function Input(
  { className, ...props },
  ref,
) {
  return <input ref={ref} className={cn(controlClasses, className)} {...props} />
})

export const Select = forwardRef<HTMLSelectElement, ComponentPropsWithoutRef<'select'>>(
  function Select({ className, ...props }, ref) {
    return <select ref={ref} className={cn(controlClasses, 'pr-8', className)} {...props} />
  },
)

export const Textarea = forwardRef<HTMLTextAreaElement, ComponentPropsWithoutRef<'textarea'>>(
  function Textarea({ className, ...props }, ref) {
    return (
      <textarea ref={ref} className={cn(controlClasses, 'min-h-28 py-2', className)} {...props} />
    )
  },
)

export function RequiredFieldsNote() {
  return <p className="text-sm text-fg-muted">Campos com * são obrigatórios.</p>
}
