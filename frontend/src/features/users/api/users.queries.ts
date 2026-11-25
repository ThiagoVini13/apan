import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { queryRoots } from '@/shared/api/query-roots'
import type { Page, Role, User, UserCreateInput, UserUpdateInput } from '@/shared/api/types'
import { DEFAULT_PAGE_SIZE } from '@/shared/lib/constants'
import { http } from '@/shared/lib/http'

export type UsersFilters = { q?: string; role?: Role; isActive?: boolean; page?: number }

export const usersApi = {
  list: (filters: UsersFilters) =>
    http.get<Page<User>>('users', { ...filters, pageSize: DEFAULT_PAGE_SIZE }),
  teachers: () => http.get<Page<User>>('users', { role: 'teacher', isActive: true, pageSize: 100 }),
  create: (data: UserCreateInput) => http.post<User>('users', data),
  update: (id: string, data: UserUpdateInput) => http.patch<User>(`users/${id}`, data),
  setActive: (id: string, active: boolean) =>
    http.post<User>(`users/${id}/${active ? 'activate' : 'deactivate'}`),
}

export const usersKeys = {
  all: queryRoots.users,
  list: (filters: UsersFilters) => [...usersKeys.all, 'list', filters] as const,
  teachers: () => [...usersKeys.all, 'teachers'] as const,
}

export function useUsers(filters: UsersFilters) {
  return useQuery({
    queryKey: usersKeys.list(filters),
    queryFn: () => usersApi.list(filters),
    placeholderData: keepPreviousData,
  })
}

export function useTeachers() {
  return useQuery({
    queryKey: usersKeys.teachers(),
    queryFn: usersApi.teachers,
    select: (page) => page.items,
  })
}

function useInvalidateUsers() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: queryRoots.users })
}

export function useInviteUser() {
  const invalidate = useInvalidateUsers()
  return useMutation({
    mutationFn: usersApi.create,
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useUpdateUser() {
  const invalidate = useInvalidateUsers()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UserUpdateInput }) => usersApi.update(id, data),
    onSuccess: invalidate,
    meta: { handlesErrors: true },
  })
}

export function useSetUserActive() {
  const invalidate = useInvalidateUsers()
  return useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => usersApi.setActive(id, active),
    onSuccess: invalidate,
  })
}
