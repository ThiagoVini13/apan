import type {
  LoginInput,
  PasswordChangeInput,
  PasswordResetInput,
  TokenResponse,
} from '@/shared/api/types'
import { http } from '@/shared/lib/http'

export const authApi = {
  login: (data: LoginInput) =>
    http.post<TokenResponse>('auth/login', data, { skipAuthRefresh: true }),
  forgotPassword: (email: string) =>
    http.post<void>('auth/password/forgot', { email }, { skipAuthRefresh: true }),
  resetPassword: (data: PasswordResetInput) =>
    http.post<void>('auth/password/reset', data, { skipAuthRefresh: true }),
  changePassword: (data: PasswordChangeInput) => http.post<void>('auth/password/change', data),
}
