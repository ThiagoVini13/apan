import { useMutation, useQueryClient } from '@tanstack/react-query'
import { sessionKeys, useStartSession } from '@/shared/session/session'
import { authApi } from './auth.api'

export function useLogin() {
  const startSession = useStartSession()
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: startSession,
    meta: { handlesErrors: true },
  })
}

export function useForgotPassword() {
  return useMutation({ mutationFn: authApi.forgotPassword, meta: { handlesErrors: true } })
}

export function useResetPassword() {
  return useMutation({ mutationFn: authApi.resetPassword, meta: { handlesErrors: true } })
}

export function useChangePassword() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: authApi.changePassword,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sessionKeys.all }),
    meta: { handlesErrors: true },
  })
}
