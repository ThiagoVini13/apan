import { screen, within } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { expectNoA11yViolations } from '@/test/a11y'
import { admin } from '@/test/db'
import { renderApp } from '@/test/render'
import { server } from '@/test/server'

const PATH = '/reports?from=2026-11-01&to=2026-11-30'

describe('reports page', () => {
  it('shows totals, classes and students for the period', async () => {
    renderApp(PATH, { as: admin })

    expect(
      await screen.findByRole('heading', { name: 'Totais de 01/11/2026 a 30/11/2026' }),
    ).toBeInTheDocument()
    expect(screen.getByText('78,6%')).toBeInTheDocument()
    expect(screen.getByText('20 dias letivos no período')).toBeInTheDocument()
    const table = within(
      await screen.findByRole('region', { name: 'Tabela de frequência por aluno' }),
    )
    expect(table.getByRole('rowheader', { name: 'Bruno Martins' })).toBeInTheDocument()
    expect(table.getByText(/abaixo do mínimo de 75%/)).toBeInTheDocument()
    await expectNoA11yViolations()
  })

  it('filters to students below the minimum', async () => {
    const { user } = renderApp(PATH, { as: admin })
    await screen.findByRole('region', { name: 'Tabela de frequência por aluno' })

    await user.click(screen.getByLabelText('Mostrar só alunos abaixo de 75%'))

    const table = within(screen.getByRole('region', { name: 'Tabela de frequência por aluno' }))
    expect(table.queryByRole('rowheader', { name: 'Alice Souza' })).not.toBeInTheDocument()
    expect(table.getByRole('rowheader', { name: 'Bruno Martins' })).toBeInTheDocument()
  })

  it('does not query an inverted period', async () => {
    const calls = vi.fn()
    server.use(
      http.get('/api/v1/reports/attendance/summary', () => {
        calls()
        return HttpResponse.json({})
      }),
    )
    renderApp('/reports?from=2026-11-30&to=2026-11-01', { as: admin })

    expect(
      (await screen.findAllByText('A data final deve ser igual ou posterior à data inicial.'))
        .length,
    ).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: 'Exportar CSV' })).toBeDisabled()
    expect(calls).not.toHaveBeenCalled()
  })

  it('downloads the spreadsheet', async () => {
    const createUrl = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:report')
    const downloads: string[] = []
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      downloads.push(this.download)
    })
    const { user } = renderApp(PATH, { as: admin })
    await screen.findByText('78,6%')

    await user.click(screen.getByRole('button', { name: 'Exportar CSV' }))

    expect(await screen.findByText('Planilha CSV gerada.')).toBeInTheDocument()
    expect(createUrl).toHaveBeenCalledTimes(1)
    expect(createUrl.mock.calls[0]?.[0]).toHaveProperty('type', 'text/csv;charset=utf-8')
    expect(downloads).toEqual(['frequencia_2026-11-01_2026-11-30.csv'])
  })
})
