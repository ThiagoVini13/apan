export function phoneDigits(value: string): string {
  return value.replace(/\D/g, '').slice(0, 11)
}

export function maskPhone(value: string): string {
  const digits = phoneDigits(value)
  if (digits.length <= 2) return digits.length ? `(${digits}` : ''
  const area = digits.slice(0, 2)
  const rest = digits.slice(2)
  const split = rest.length > 8 ? 5 : 4
  if (rest.length <= split) return `(${area}) ${rest}`
  return `(${area}) ${rest.slice(0, split)}-${rest.slice(split)}`
}

export function isValidPhone(value: string): boolean {
  const digits = phoneDigits(value)
  if (digits.length !== 10 && digits.length !== 11) return false
  if (digits[0] === '0') return false
  return digits.length === 10 || digits[2] === '9'
}
