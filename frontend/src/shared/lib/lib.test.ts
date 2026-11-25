import { describe, expect, it } from 'vitest'
import { calculateAge, isIsoDate, monthRange } from './date'
import { formatDate, formatPercent, formatPhone } from './format'
import { isValidPhone, maskPhone, phoneDigits } from './phone'

describe('phone', () => {
  it.each([
    ['9', '(9'],
    ['92', '(92'],
    ['9299', '(92) 99'],
    ['929912345', '(92) 9912-345'],
    ['9232345678', '(92) 3234-5678'],
    ['92991234567', '(92) 99123-4567'],
    ['(92) 99123-45678', '(92) 99123-4567'],
  ])('masks %s as %s', (input, expected) => {
    expect(maskPhone(input)).toBe(expected)
  })

  it('validates area code and mobile prefix', () => {
    expect(isValidPhone('(92) 99123-4567')).toBe(true)
    expect(isValidPhone('(92) 3234-5678')).toBe(true)
    expect(isValidPhone('(92) 89123-4567')).toBe(false)
    expect(isValidPhone('(02) 3234-5678')).toBe(false)
    expect(isValidPhone('99123-4567')).toBe(false)
  })

  it('keeps only digits', () => {
    expect(phoneDigits('(92) 99123-4567')).toBe('92991234567')
  })
})

describe('date', () => {
  it('calculates age on a reference date', () => {
    expect(calculateAge('2016-11-24', '2026-11-24')).toBe(10)
    expect(calculateAge('2016-11-25', '2026-11-24')).toBe(9)
  })

  it('validates ISO dates', () => {
    expect(isIsoDate('2026-02-28')).toBe(true)
    expect(isIsoDate('2026-02-30')).toBe(false)
    expect(isIsoDate('28/02/2026')).toBe(false)
  })

  it('returns month ranges', () => {
    expect(monthRange('2026-11-24')).toEqual({ from: '2026-11-01', to: '2026-11-30' })
    expect(monthRange('2026-03-10', 1)).toEqual({ from: '2026-02-01', to: '2026-02-28' })
  })
})

describe('format', () => {
  it('formats percentages in pt-BR', () => {
    expect(formatPercent(87.5)).toBe('87,5%')
    expect(formatPercent(100, 0)).toBe('100%')
    expect(formatPercent(null)).toBe('—')
  })

  it('formats dates and phones', () => {
    expect(formatDate('2026-11-24')).toBe('24/11/2026')
    expect(formatPhone('92991234567')).toBe('(92) 99123-4567')
  })
})
