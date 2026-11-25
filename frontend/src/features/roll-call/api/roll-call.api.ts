import type { RollCall, RollCallSheet, RollCallUpsertInput } from '@/shared/api/types'
import { http } from '@/shared/lib/http'
import type { SheetParams } from '../types'

export const rollCallApi = {
  sheet: ({ classId, subjectId, date }: SheetParams) =>
    http.get<RollCallSheet>('roll-calls/sheet', { classId, subjectId, date }),
  save: (data: RollCallUpsertInput) => http.put<RollCall>('roll-calls', data),
}
