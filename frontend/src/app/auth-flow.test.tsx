import { screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { expectNoA11yViolations } from '@/test/a11y'
import { admin, teacher } from '@/test/db'
import { renderApp } from '@/test/render'
import { server, sessionCookie } from '@/test/server'

describe('authentication', () => {
  it('sends visitors without a session to the login page', async () => {
    renderApp('/reports')

    expect(await screen.findByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
    await expectNoA11yViolations()
  })

  it('logs in and returns to the requested page', async () => {
    const { user, router } = renderApp('/login?next=%2Freports')

    await user.type(await screen.findByLabelText(/E-mail/), teacher.email)
    await user.type(screen.getByLabelText(/Senha/), 'senha-da-professora')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('heading', { name: 'Relatórios', level: 1 })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/reports')
  })

  it('shows a clear message for wrong credentials', async () => {
    const { user } = renderApp('/login')

    await user.type(await screen.findByLabelText(/E-mail/), teacher.email)
    await user.type(screen.getByLabelText(/Senha/), 'errada-errada')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('E-mail ou senha incorretos.')).toBeInTheDocument()
  })

  it('validates the form before calling the API', async () => {
    const { user } = renderApp('/login')

    await user.click(await screen.findByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('Informe o e-mail.')).toBeInTheDocument()
    expect(screen.getByLabelText(/E-mail/)).toHaveAttribute('aria-invalid', 'true')
  })

  it('restores the session from the refresh cookie on reload', async () => {
    sessionCookie.email = teacher.email
    renderApp('/')

    expect(await screen.findByRole('heading', { name: 'Olá, Ana' })).toBeInTheDocument()
  })

  it('renews an expired access token once and repeats the request', async () => {
    const seenTokens: (string | null)[] = []
    server.use(
      http.get('/api/v1/dashboard/today', ({ request }) => {
        seenTokens.push(request.headers.get('Authorization'))
        if (seenTokens.length === 1) {
          return HttpResponse.json({ code: 'invalid_token' }, { status: 401 })
        }
        return HttpResponse.json({
          date: '2026-11-24',
          schoolYearId: null,
          schoolYearName: null,
          isSchoolDay: false,
          totalClasses: 0,
          totalStudents: 0,
          rollCallsExpected: 0,
          rollCallsDone: 0,
          presenceRateToday: null,
          presenceRateLast30Days: null,
          pendingRollCalls: [],
          lowAttendanceStudents: [],
        })
      }),
    )
    renderApp('/', { as: teacher })

    expect(await screen.findByText('Nenhum ano letivo atual')).toBeInTheDocument()
    expect(seenTokens.slice(0, 2)).toEqual([
      `Bearer token-for:${teacher.email}`,
      `Bearer token-for:${teacher.email}`,
    ])
  })

  it('blocks administration pages for teachers', async () => {
    renderApp('/admin/users', { as: teacher })

    expect(await screen.findByRole('heading', { name: 'Sem permissão' })).toBeInTheDocument()
  })

  it('lets administrators open administration pages', async () => {
    renderApp('/admin', { as: admin })

    expect(await screen.findByRole('heading', { name: 'Administração' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Usuários' }).length).toBeGreaterThan(0)
  })

  it('logs out', async () => {
    const { user, router } = renderApp('/', { as: teacher })

    await user.click((await screen.findAllByRole('button', { name: 'Sair' }))[0])

    await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
    expect(sessionCookie.email).toBeNull()
  })
})
