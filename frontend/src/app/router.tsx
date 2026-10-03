import { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import Layout from '@/shared/ui/Layout'

const DashboardPage = lazy(() => import('@/features/dashboard/pages/DashboardPage'))
const StudentsPage  = lazy(() => import('@/features/students/pages/StudentsPage'))
const RollCallPage  = lazy(() => import('@/features/roll-call/pages/RollCallPage'))
const ReportsPage   = lazy(() => import('@/features/reports/pages/ReportsPage'))

const Loader = () => (
  <div className="flex items-center justify-center h-32 text-slate-400">Carregando...</div>
)

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true,          element: <Suspense fallback={<Loader />}><DashboardPage /></Suspense> },
      { path: 'students',     element: <Suspense fallback={<Loader />}><StudentsPage /></Suspense>  },
      { path: 'roll-call',    element: <Suspense fallback={<Loader />}><RollCallPage /></Suspense>  },
      { path: 'reports',      element: <Suspense fallback={<Loader />}><ReportsPage /></Suspense>   },
    ],
  },
])
