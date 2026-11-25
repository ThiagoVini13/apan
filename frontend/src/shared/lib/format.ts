import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'

const percentFormatters = new Map<number, Intl.NumberFormat>()

function percentFormatter(digits: number) {
  let formatter = percentFormatters.get(digits)
  if (!formatter) {
    formatter = new Intl.NumberFormat('pt-BR', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    })
    percentFormatters.set(digits, formatter)
  }
  return formatter
}

export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return '—'
  return `${percentFormatter(digits).format(value)}%`
}

const integerFormatter = new Intl.NumberFormat('pt-BR')

export function formatNumber(value: number): string {
  return integerFormatter.format(value)
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return format(parseISO(iso), 'dd/MM/yyyy')
}

export function formatDateLong(iso: string): string {
  return format(parseISO(iso), "EEEE, d 'de' MMMM 'de' yyyy", { locale: ptBR })
}

export function formatDateTime(iso: string): string {
  return format(parseISO(iso), "dd/MM/yyyy 'às' HH:mm")
}

export function formatPhone(digits: string): string {
  if (digits.length === 11)
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
  if (digits.length === 10)
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`
  return digits
}
