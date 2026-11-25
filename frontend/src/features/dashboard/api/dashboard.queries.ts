import { useQuery } from '@tanstack/react-query'
import { queryRoots } from '@/shared/api/query-roots'
import type { DashboardToday } from '@/shared/api/types'
import { http } from '@/shared/lib/http'

export const dashboardKeys = {
  all: queryRoots.dashboard,
  today: () => [...dashboardKeys.all, 'today'] as const,
}

export function useDashboardToday() {
  return useQuery({
    queryKey: dashboardKeys.today(),
    queryFn: () => http.get<DashboardToday>('dashboard/today'),
  })
}
