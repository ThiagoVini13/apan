import { describe, expect, it } from 'vitest'
import { periodShortcuts } from './periods'

const year = {
  id: 'y',
  name: '2026',
  startsOn: '2026-02-02',
  endsOn: '2026-12-15',
  isCurrent: true,
}
const terms = [
  {
    id: 't3',
    schoolYearId: 'y',
    name: '3º bimestre',
    startsOn: '2026-07-27',
    endsOn: '2026-10-02',
  },
  {
    id: 't4',
    schoolYearId: 'y',
    name: '4º bimestre',
    startsOn: '2026-10-05',
    endsOn: '2026-12-15',
  },
]

describe('period shortcuts', () => {
  it('offers month, previous month, current term and school year up to today', () => {
    expect(periodShortcuts('2026-11-24', year, terms)).toEqual([
      { label: 'Este mês', from: '2026-11-01', to: '2026-11-24' },
      { label: 'Mês passado', from: '2026-10-01', to: '2026-10-31' },
      { label: '4º bimestre', from: '2026-10-05', to: '2026-11-24' },
      { label: 'Ano letivo', from: '2026-02-02', to: '2026-11-24' },
    ])
  })

  it('omits the term and year shortcuts when there is no school year', () => {
    expect(periodShortcuts('2026-11-24', null, []).map((p) => p.label)).toEqual([
      'Este mês',
      'Mês passado',
    ])
  })
})
