import { screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { expectNoA11yViolations } from '@/test/a11y'
import { db, teacher } from '@/test/db'
import { renderApp } from '@/test/render'

const PATH = '/roll-call?classId=class-5a&subjectId=subject-math'

async function openSheet() {
  const utils = renderApp(PATH, { as: teacher })
  await screen.findByRole('heading', { name: /5º Ano A · 3 alunos/ })
  return utils
}

function row(name: string) {
  return within(screen.getByRole('group', { name: `Situação de ${name}` }))
}

describe('roll call page', () => {
  it('lists the roster in alphabetical order with nothing marked', async () => {
    await openSheet()

    const names = screen
      .getAllByRole('group', { name: /^Situação de / })
      .map((g) => g.getAttribute('aria-label'))
    expect(names).toEqual([
      'Situação de Alice Souza',
      'Situação de Bruno Martins',
      'Situação de Carla Ferreira',
    ])
    expect(screen.getByText('3 sem marcação')).toBeInTheDocument()
    await expectNoA11yViolations()
  })

  it('does not save until every student is marked and focuses the first pending one', async () => {
    const { user } = await openSheet()

    await user.click(row('Alice Souza').getByRole('button', { name: 'Presente' }))
    await user.click(screen.getByRole('button', { name: 'Salvar frequência' }))

    expect(await screen.findByText('Faltam marcar 2 alunos antes de salvar.')).toBeInTheDocument()
    expect(row('Bruno Martins').getByRole('button', { name: 'Presente' })).toHaveFocus()
    expect(db.savedRollCalls).toHaveLength(0)
  })

  it('saves marks and notes', async () => {
    const { user } = await openSheet()

    await user.click(screen.getByRole('button', { name: 'Marcar todos como presentes' }))
    await user.click(row('Bruno Martins').getByRole('button', { name: 'Ausente' }))
    expect(row('Bruno Martins').getByRole('button', { name: 'Ausente' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    await user.type(screen.getByLabelText('Anotações da aula'), 'Frações; Bruno sem material.')
    expect(screen.getByText('28 de 1000 caracteres')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Salvar frequência' }))

    expect(await screen.findByText(/Chamada de .* salva\./)).toBeInTheDocument()
    expect(db.savedRollCalls).toHaveLength(1)
    const saved = db.savedRollCalls[0]
    expect(saved.notes).toBe('Frações; Bruno sem material.')
    expect(saved.classId).toBe('class-5a')
    expect(saved.subjectId).toBe('subject-math')
    expect(Object.fromEntries(saved.attendances.map((a) => [a.studentId, a.status]))).toEqual({
      'student-alice': 'present',
      'student-bruno': 'absent',
      'student-carla': 'present',
    })
  })

  it('shows a locked roll call as read only with the reason', async () => {
    db.sheetEditable = false
    db.marks = { 'student-alice': 'present', 'student-bruno': 'absent', 'student-carla': 'present' }
    await openSheet()

    expect(
      screen.getByText(/O prazo para registrar ou alterar esta chamada terminou/),
    ).toBeInTheDocument()
    expect(row('Bruno Martins').getByRole('button', { name: 'Ausente' })).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Salvar frequência' })).not.toBeInTheDocument()
  })

  it('asks for confirmation before leaving with unsaved marks', async () => {
    const { user } = await openSheet()

    await user.click(row('Alice Souza').getByRole('button', { name: 'Ausente' }))
    await user.click(screen.getAllByRole('link', { name: 'Alunos' })[0])

    expect(await screen.findByRole('dialog', { name: 'Sair sem salvar?' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(screen.getByRole('heading', { name: 'Chamada', level: 1 })).toBeInTheDocument()
  })
})
