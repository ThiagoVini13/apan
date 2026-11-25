import { lazy } from 'react'

export const UsersPage = lazy(() => import('./pages/UsersPage'))
export { useTeachers } from './api/users.queries'
