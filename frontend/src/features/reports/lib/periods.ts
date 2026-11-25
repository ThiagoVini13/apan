import type { SchoolYear, Term } from '@/shared/api/types'
import { monthRange, type IsoDate } from '@/shared/lib/date'

export type Period = { label: string; from: IsoDate; to: IsoDate }

function upToToday(to: IsoDate, today: IsoDate) {
  return to > today ? today : to
}

export function periodShortcuts(today: IsoDate, year: SchoolYear | null, terms: Term[]): Period[] {
  const thisMonth = monthRange(today)
  const lastMonth = monthRange(today, 1)
  const shortcuts: Period[] = [
    { label: 'Este mês', from: thisMonth.from, to: upToToday(thisMonth.to, today) },
    { label: 'Mês passado', ...lastMonth },
  ]
  const currentTerm = terms.find((term) => term.startsOn <= today && today <= term.endsOn)
  if (currentTerm) {
    shortcuts.push({
      label: currentTerm.name,
      from: currentTerm.startsOn,
      to: upToToday(currentTerm.endsOn, today),
    })
  }
  if (year) {
    shortcuts.push({ label: 'Ano letivo', from: year.startsOn, to: upToToday(year.endsOn, today) })
  }
  return shortcuts
}

export function defaultPeriod(today: IsoDate): Period {
  const month = monthRange(today)
  return { label: 'Este mês', from: month.from, to: upToToday(month.to, today) }
}
