import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { queryRoots } from '@/shared/api/query-roots'
import type { AuditLog, Page } from '@/shared/api/types'
import { http } from '@/shared/lib/http'

export type AuditFilters = { action?: string; from?: string; to?: string; page: number }

const auditKeys = {
  all: queryRoots.audit,
  list: (filters: AuditFilters) => [...auditKeys.all, 'list', filters] as const,
}

export function useAuditLogs(filters: AuditFilters) {
  return useQuery({
    queryKey: auditKeys.list(filters),
    queryFn: () => http.get<Page<AuditLog>>('audit-logs', { ...filters, pageSize: 50 }),
    placeholderData: keepPreviousData,
  })
}
