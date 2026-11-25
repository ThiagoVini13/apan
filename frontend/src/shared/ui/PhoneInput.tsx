import { forwardRef, type ComponentPropsWithoutRef } from 'react'
import { maskPhone } from '@/shared/lib/phone'
import { Input } from './Field'

type PhoneInputProps = Omit<ComponentPropsWithoutRef<'input'>, 'onChange' | 'value' | 'type'> & {
  value: string
  onChange: (value: string) => void
}

export const PhoneInput = forwardRef<HTMLInputElement, PhoneInputProps>(function PhoneInput(
  { value, onChange, ...props },
  ref,
) {
  return (
    <Input
      ref={ref}
      type="tel"
      inputMode="tel"
      autoComplete="tel"
      placeholder="(92) 99123-4567"
      value={maskPhone(value)}
      onChange={(event) => onChange(maskPhone(event.target.value))}
      {...props}
    />
  )
})
