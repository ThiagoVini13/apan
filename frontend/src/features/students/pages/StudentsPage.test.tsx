import { screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { expectNoA11yViolations } from '@/test/a11y'
import { db, teacher } from '@/test/db'
import { renderApp } from '@/test/render'

describe('students page', () => {
  it('lists students with their class and attendance', async () => {
    renderApp('/students', { as: teacher })

    expect(await screen.findByText('3 aluno(s) encontrado(s)')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Editar Alice Souza' }).length).toBeGreaterThan(0)
    await expectNoA11yViolations()
  })

  it('requires a guardian when the student is a minor', async () => {
    const { user } = renderApp('/students/new', { as: teacher })
    const dialog = await screen.findByRole('dialog', { name: 'Novo aluno' })
    const form = within(dialog)

    await user.type(form.getByLabelText(/Nome completo/), 'Davi Lima')
    await user.type(form.getByLabelText(/Data de nascimento/), '2016-05-10')
    await user.selectOptions(form.getByLabelText(/^Turma/), 'class-5a')
    await user.click(form.getByRole('button', { name: 'Cadastrar aluno' }))

    expect(await form.findByText(/precisam de um responsável/)).toBeInTheDocument()
    expect(form.getByLabelText(/Nome do responsável/)).toHaveAttribute('aria-invalid', 'true')
    expect(db.createdStudents).toHaveLength(0)
    await expectNoA11yViolations(dialog)
  })

  it('registers a student with a guardian', async () => {
    const { user, router } = renderApp('/students/new', { as: teacher })
    const form = within(await screen.findByRole('dialog', { name: 'Novo aluno' }))

    await user.type(form.getByLabelText(/Nome completo/), 'Davi Lima')
    await user.type(form.getByLabelText(/Data de nascimento/), '2016-05-10')
    await user.selectOptions(form.getByLabelText(/^Turma/), 'class-5a')
    await user.type(form.getByLabelText(/Nome do responsável/), 'Rita Lima')
    await user.type(form.getByLabelText(/Telefone/), '92988887777')
    expect(form.getByLabelText(/Telefone/)).toHaveValue('(92) 98888-7777')
    await user.selectOptions(form.getByLabelText(/Parentesco/), 'mother')
    await user.click(form.getByRole('button', { name: 'Cadastrar aluno' }))

    expect(
      await screen.findByText(/Davi Lima cadastrado\(a\)\. Matrícula 202600099\./),
    ).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/students')
    expect(db.createdStudents).toEqual([
      {
        fullName: 'Davi Lima',
        birthDate: '2016-05-10',
        classId: 'class-5a',
        guardians: [
          { fullName: 'Rita Lima', phone: '92988887777', relationship: 'mother', isPrimary: true },
        ],
      },
    ])
  })
})
