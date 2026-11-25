import {
  differenceInYears,
  endOfMonth,
  format,
  isValid,
  parseISO,
  startOfMonth,
  subMonths,
} from 'date-fns'

export type IsoDate = string

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

export function toIsoDate(date: Date): IsoDate {
  return format(date, 'yyyy-MM-dd')
}

export function todayIso(): IsoDate {
  return toIsoDate(new Date())
}

export function isIsoDate(value: string | null | undefined): value is IsoDate {
  return !!value && ISO_DATE.test(value) && isValid(parseISO(value))
}

export function parseIsoDate(value: IsoDate): Date {
  return parseISO(value)
}

export function calculateAge(birthDate: IsoDate, on: IsoDate = todayIso()): number {
  return differenceInYears(parseISO(on), parseISO(birthDate))
}

export function monthRange(reference: IsoDate = todayIso(), monthsAgo = 0) {
  const base = subMonths(parseISO(reference), monthsAgo)
  return { from: toIsoDate(startOfMonth(base)), to: toIsoDate(endOfMonth(base)) }
}

export function clampRange(from: IsoDate, to: IsoDate, min: IsoDate, max: IsoDate) {
  return { from: from < min ? min : from, to: to > max ? max : to }
}
