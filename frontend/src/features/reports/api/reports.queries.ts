import { keepPreviousData, useMutation, useQuery } from '@tanstack/react-query'
import type { ExportFormat } from '@/shared/api/types'
import { saveBlob } from '@/shared/lib/download'
import type { ReportParams } from '../types'
import { reportsApi } from './reports.api'
import { reportsKeys } from './reports.keys'

const disabledParams: ReportParams = { from: '', to: '' }

export function useReportSummary(params: ReportParams | null) {
  return useQuery({
    queryKey: reportsKeys.summary(params ?? disabledParams),
    queryFn: () => reportsApi.summary(params ?? disabledParams),
    enabled: params !== null,
    placeholderData: keepPreviousData,
  })
}

export function useReportStudents(params: ReportParams | null) {
  return useQuery({
    queryKey: reportsKeys.students(params ?? disabledParams),
    queryFn: () => reportsApi.students(params ?? disabledParams),
    enabled: params !== null,
    placeholderData: keepPreviousData,
    select: (list) => list.items,
  })
}

export function useReportByClass(params: ReportParams | null) {
  return useQuery({
    queryKey: reportsKeys.byClass(params ?? disabledParams),
    queryFn: () => reportsApi.byClass(params ?? disabledParams),
    enabled: params !== null,
    placeholderData: keepPreviousData,
    select: (list) => list.items,
  })
}

export function useTerms(schoolYearId: string | undefined) {
  return useQuery({
    queryKey: reportsKeys.terms(schoolYearId ?? ''),
    queryFn: () => reportsApi.terms(schoolYearId ?? ''),
    enabled: !!schoolYearId,
    staleTime: 10 * 60 * 1000,
    select: (list) => list.items,
  })
}

export function useExportReport() {
  return useMutation({
    mutationFn: async ({ params, format }: { params: ReportParams; format: ExportFormat }) => {
      const blob = await reportsApi.export(params, format)
      saveBlob(blob, `frequencia_${params.from}_${params.to}.${format}`)
    },
  })
}
