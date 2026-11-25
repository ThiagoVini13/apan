import { lazy } from 'react'

export const StudentsPage = lazy(() => import('./pages/StudentsPage'))
export const StudentCreateRoute = lazy(() =>
  import('./pages/StudentsPage').then((module) => ({ default: module.StudentCreateRoute })),
)
export const StudentEditRoute = lazy(() =>
  import('./pages/StudentsPage').then((module) => ({ default: module.StudentEditRoute })),
)
