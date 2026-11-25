import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { expectNoA11yViolations } from '@/test/a11y'
import { teacher } from '@/test/db'
import { renderApp } from '@/test/render'

describe('dashboard', () => {
  it('shows pending roll calls with a link to take them', async () => {
    renderApp('/', { as: teacher })

    const link = await screen.findByRole('link', { name: /5º Ano A · Matemática/ })
    expect(link).toHaveAttribute(
      'href',
      expect.stringContaining('/roll-call?classId=class-5a&subjectId=subject-math'),
    )
    expect(screen.getByText('82,5%')).toBeInTheDocument()
    expect(screen.getByText('Bruno Martins')).toBeInTheDocument()
    expect(document.title).toBe('Início · APAN Frequência')
    await expectNoA11yViolations()
  })

  it('offers a skip link and keyboard reachable navigation', async () => {
    const { user } = renderApp('/', { as: teacher })
    await screen.findByRole('heading', { name: 'Olá, Ana' })

    await user.tab()

    expect(screen.getByRole('link', { name: 'Pular para o conteúdo' })).toHaveFocus()
  })
})
