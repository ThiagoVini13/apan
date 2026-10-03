import { useState } from 'react'
import { useStudents } from '@/features/students/api/students.queries'
import { useClasses } from '@/features/classes/api/classes.queries'
import { StatusPill } from '@/shared/ui/StatusPill'

export default function ReportsPage() {
  const [classFilter, setClassFilter] = useState('all')
  const [dateFrom,    setDateFrom]    = useState('2026-01-01')
  const [dateTo,      setDateTo]      = useState('2026-12-31')

  const { data: classesData } = useClasses()
  const classes = classesData?.items ?? []

  const { data, isPending, isError } = useStudents({
    classId: classFilter !== 'all' ? classFilter : undefined,
  })

  const students = data?.items ?? []

  const avgRate = students.length > 0
    ? Math.round(
        students.reduce((acc, s) => acc + (s.attendanceRate ?? 0), 0) / students.length,
      )
    : 0
  const atRisk = students.filter((s) => (s.attendanceRate ?? 100) < 75).length

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Relatórios</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Presença Geral</p>
          <p className="mt-1 text-3xl font-bold text-slate-800">{avgRate}%</p>
        </div>
        <div className="rounded-xl border border-red-100 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Alunos em Risco</p>
          <p className="mt-1 text-3xl font-bold text-red-600">{atRisk}</p>
          <p className="text-xs text-slate-400 mt-1">Frequência abaixo de 75%</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Total de Alunos</p>
          <p className="mt-1 text-3xl font-bold text-slate-800">{data?.total ?? '—'}</p>
          <p className="text-xs text-slate-400 mt-1">No filtro atual</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-500">Turma</label>
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
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-500">Data início</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-500">Data fim</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
      </div>

      {/* Attendance table */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Nome</th>
              <th className="px-4 py-3 text-left font-medium">Turma</th>
              <th className="px-4 py-3 text-left font-medium">% Frequência</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isPending && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-400 animate-pulse">
                  Carregando...
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-red-500 text-sm">
                  Erro ao carregar dados.
                </td>
              </tr>
            )}
            {students.map((student) => {
              const cls    = classes.find((c) => c.id === student.classId)
              const rate   = student.attendanceRate
              const isRisk = rate != null && rate < 75
              return (
                <tr key={student.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-800">{student.fullName}</td>
                  <td className="px-4 py-3 text-slate-600">{cls?.name ?? '—'}</td>
                  <td className="px-4 py-3">
                    {rate != null
                      ? <StatusPill rate={rate} />
                      : <span className="text-slate-400 text-xs">Sem chamadas</span>
                    }
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                        isRisk
                          ? 'bg-red-100 text-red-700'
                          : 'bg-green-100 text-green-700'
                      }`}
                    >
                      {rate == null ? '—' : isRisk ? 'Atenção' : 'OK'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {data && (
        <p className="text-xs text-slate-400">
          {data.total} aluno(s) — período: {dateFrom} a {dateTo}
        </p>
      )}
    </div>
  )
}
