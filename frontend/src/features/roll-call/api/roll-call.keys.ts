import { queryRoots } from '@/shared/api/query-roots'
import type { SheetParams } from '../types'

export const rollCallKeys = {
  all: queryRoots.rollCalls,
  sheets: () => [...rollCallKeys.all, 'sheet'] as const,
  sheet: (params: SheetParams) => [...rollCallKeys.sheets(), params] as const,
}
