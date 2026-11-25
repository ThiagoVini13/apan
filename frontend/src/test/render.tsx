import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RouterProvider, createMemoryRouter } from 'react-router-dom'
import { Providers } from '@/app/providers'
import { createQueryClient } from '@/app/query-client'
import { routes } from '@/app/router'
import { tokenStore } from '@/shared/lib/auth-token'
import type { Me } from '@/shared/api/types'
import { sessionCookie } from './server'

type RenderOptions = { as?: Me | null }

export function renderApp(path: string, { as = null }: RenderOptions = {}) {
  if (as) {
    sessionCookie.email = as.email
    tokenStore.set(`token-for:${as.email}`)
  }
  const queryClient = createQueryClient()
  queryClient.setDefaultOptions({
    queries: { ...queryClient.getDefaultOptions().queries, retry: false },
  })
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  const user = userEvent.setup()
  const utils = render(
    <Providers queryClient={queryClient}>
      <RouterProvider router={router} />
    </Providers>,
  )
  return { ...utils, user, router, queryClient }
}
