import type { VariantProps } from 'class-variance-authority'
import { forwardRef, type ComponentPropsWithoutRef } from 'react'
import { cn } from '@/shared/lib/cn'
import { buttonVariants } from './button-variants'
import { SpinnerIcon } from './icons'

type ButtonProps = ComponentPropsWithoutRef<'button'> &
  VariantProps<typeof buttonVariants> & {
    isPending?: boolean
    pendingLabel?: string
  }

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    className,
    variant,
    size,
    isPending = false,
    pendingLabel,
    disabled,
    children,
    type = 'button',
    ...props
  },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={disabled || isPending}
      aria-busy={isPending || undefined}
      {...props}
    >
      {isPending && <SpinnerIcon className="size-4 animate-spin" />}
      {isPending && pendingLabel ? pendingLabel : children}
    </button>
  )
})
