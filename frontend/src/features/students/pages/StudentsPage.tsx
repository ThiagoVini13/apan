import { useState } from 'react'
import { useStudents, useCreateStudent } from '@/features/students/api/students.queries'
import { useClasses } from '@/features/classes/api/classes.queries'
import { StatusPill } from '@/shared/ui/StatusPill'
import type { StudentCreateInput } from '@/shared/types'

const EMPTY_FORM: StudentCreateInput = {
  fullName: '',
  enrollmentNumber: '',
  classId: '',
  birthDate: '',
}

export default function StudentsPage() {
  const [search,      setSearch]     = useState('')
  const [classFilter, setClassFilter] = useState('all')
  const [showForm,    setShowForm]   = useState(false)
  const [form,        setForm]       = useState<StudentCreateInput>(EMPTY_FORM)

  const { data: classesData } = useClasses()
  const classes = classesData?.items ?? []

  const { data, isPending, isError } = useStudents({
    q:       search || undefined,
    classId: classFilter !== 'all' ? classFilter : undefined,
  })

  const createStudent = useCreateStudent()

  const defaultClassId = classes[0]?.id ?? ''

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    createStudent.mutate(
      { ...form, classId: form.classId || defaultClassId },
      {
        onSuccess: () => {
          setForm(EMPTY_FORM)
          setShowForm(false)
        },
      },
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-slate-800">Alunos</h1>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          {showForm ? 'Cancelar' : '+ Novo Aluno'}
        </button>
      </div>

      {/* New student form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-blue-200 bg-blue-50 p-5 space-y-4"
        >
          <h2 className="text-sm font-semibold text-slate-700">Novo Aluno</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Nome completo</label>
              <input
                required
                type="text"
                value={form.fullName}
                onChange={(e) => setForm((f) => ({ ...f, fullName: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="Nome do aluno"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Matrícula</label>
              <input
                required
                type="text"
                value={form.enrollmentNumber}
                onChange={(e) => setForm((f) => ({ ...f, enrollmentNumber: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="2026016"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Data de nascimento</label>
              <input
                type="date"
                value={form.birthDate ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, birthDate: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Turma</label>
              <select
                value={form.classId || defaultClassId}
                onChange={(e) => setForm((f) => ({ ...f, classId: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                {classes.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>
          {createStudent.isError && (
            <p className="text-xs text-red-600">Erro ao salvar. Verifique os dados e tente novamente.</p>
          )}
          <button
            type="submit"
            disabled={createStudent.isPending}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {createStudent.isPending ? 'Salvando...' : 'Salvar Aluno'}
          </button>
        </form>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Buscar por nome..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 w-56"
        />
        <select
          value={classFilter}
          onChange={(e) => setClassFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          <option value="all">Todas as turmas</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {/* Students table */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Matrícula</th>
              <th className="px-4 py-3 text-left font-medium">Nome</th>
              <th className="px-4 py-3 text-left font-medium">Turma</th>
              <th className="px-4 py-3 text-left font-medium">Frequência</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isPending && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400 animate-pulse">
                  Carregando alunos...
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-red-500 text-sm">
                  Erro ao carregar alunos.
                </td>
              </tr>
            )}
            {!isPending && !isError && data?.items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                  Nenhum aluno encontrado.
                </td>
              </tr>
            )}
            {data?.items.map((student) => {
              const cls = classes.find((c) => c.id === student.classId)
              return (
                <tr key={student.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-500">{student.enrollmentNumber}</td>
                  <td className="px-4 py-3 font-medium text-slate-800">{student.fullName}</td>
                  <td className="px-4 py-3 text-slate-600">{cls?.name ?? '—'}</td>
                  <td className="px-4 py-3">
                    {student.attendanceRate != null
                      ? <StatusPill rate={student.attendanceRate} />
                      : <span className="text-slate-400 text-xs">Sem chamadas</span>
                    }
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {data && (
        <p className="text-xs text-slate-400">{data.total} aluno(s) encontrado(s)</p>
      )}
    </div>
  )
}
