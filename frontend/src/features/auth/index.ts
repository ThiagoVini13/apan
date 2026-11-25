import { lazy } from 'react'

export const LoginPage = lazy(() => import('./pages/LoginPage'))
export const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'))
export const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'))
export const ChangePasswordPage = lazy(() => import('./pages/ChangePasswordPage'))
