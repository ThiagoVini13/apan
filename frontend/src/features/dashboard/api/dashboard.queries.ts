import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/lib/api'
import type { DashboardToday } from '@/shared/types'

export const dashboardKeys = {
  today: ['dashboard', 'today'] as const,
}

export function useDashboardToday() {
  return useQuery({
    queryKey: dashboardKeys.today,
    queryFn: () => api.get<DashboardToday>('/dashboard/today'),
  })
}
