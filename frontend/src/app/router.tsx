import { lazy, Suspense, type ReactNode } from 'react'
import { createBrowserRouter, type RouteObject } from 'react-router-dom'
import { AuditPage } from '@/features/audit'
import {
  ChangePasswordPage,
  ForgotPasswordPage,
  LoginPage,
  ResetPasswordPage,
} from '@/features/auth'
import { ClassesPage } from '@/features/classes'
import { DashboardPage } from '@/features/dashboard'
import { ReportsPage } from '@/features/reports'
import { RollCallPage } from '@/features/roll-call'
import { SchoolYearsPage } from '@/features/school-years'
import { StudentCreateRoute, StudentEditRoute, StudentsPage } from '@/features/students'
import { SubjectsPage } from '@/features/subjects'
import { UsersPage } from '@/features/users'
import { RequireAuth, RequireRole } from '@/shared/session/guards'
import { LoadingList } from '@/shared/ui/States'
import { AppShell } from './layouts/AppShell'
import { NotFoundPage, RouteErrorPage } from './pages/ErrorPages'

const AdminHomePage = lazy(() => import('./pages/AdminHomePage'))
const AccountPage = lazy(() => import('./pages/AccountPage'))

function page(element: ReactNode) {
  return <Suspense fallback={<LoadingList label="Carregando…" rows={3} />}>{element}</Suspense>
}

export const routes: RouteObject[] = [
  { path: '/login', element: page(<LoginPage />), errorElement: <RouteErrorPage /> },
  { path: '/forgot-password', element: page(<ForgotPasswordPage />) },
  { path: '/reset-password', element: page(<ResetPasswordPage />) },
  {
    element: <RequireAuth />,
    errorElement: <RouteErrorPage />,
    children: [
      {
        element: <AppShell />,
        errorElement: <RouteErrorPage />,
        children: [
          { index: true, element: page(<DashboardPage />) },
          { path: 'roll-call', element: page(<RollCallPage />) },
          {
            path: 'students',
            element: page(<StudentsPage />),
            children: [
              { path: 'new', element: page(<StudentCreateRoute />) },
              { path: ':studentId/edit', element: page(<StudentEditRoute />) },
            ],
          },
          { path: 'reports', element: page(<ReportsPage />) },
          { path: 'change-password', element: page(<ChangePasswordPage />) },
          { path: 'account', element: page(<AccountPage />) },
          {
            path: 'admin',
            element: <RequireRole roles={['admin']} />,
            children: [
              { index: true, element: page(<AdminHomePage />) },
              { path: 'users', element: page(<UsersPage />) },
              { path: 'classes', element: page(<ClassesPage />) },
              { path: 'subjects', element: page(<SubjectsPage />) },
              { path: 'school-years', element: page(<SchoolYearsPage />) },
              { path: 'audit', element: page(<AuditPage />) },
            ],
          },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
]

export function createAppRouter() {
  return createBrowserRouter(routes)
}
