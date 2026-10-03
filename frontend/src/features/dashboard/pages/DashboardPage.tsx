import { useDashboardToday } from '@/features/dashboard/api/dashboard.queries'

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-bold text-slate-800">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </div>
  )
}

export default function DashboardPage() {
  const { data, isPending, isError } = useDashboardToday()

  if (isPending) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold text-slate-800">Início</h1>
        <p className="text-slate-500 text-sm animate-pulse">Carregando...</p>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold text-slate-800">Início</h1>
        <p className="text-red-500 text-sm">Erro ao carregar dados. Verifique se o backend está rodando.</p>
      </div>
    )
  }

  const presenceRate = data.presenceRate != null
    ? `${Math.round(data.presenceRate)}%`
    : '—'

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-800">Início</h1>

      {/* Summary cards */}
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Resumo</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Total de Alunos"  value={data.totalStudents} />
          <StatCard label="Total de Turmas"  value={data.totalClasses} />
          <StatCard label="Chamadas Hoje"    value={data.rollCallsCompleted}
                    sub={data.rollCallsCompleted === 0 ? 'Nenhuma registrada' : undefined} />
          <StatCard label="Presença Média"   value={presenceRate} />
        </div>
      </section>

      {/* At-risk students */}
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
          Alunos com Frequência Abaixo de 75%
        </h2>
        {data.lowAttendanceStudents.length === 0 ? (
          <p className="text-slate-500 text-sm">Nenhum aluno em risco.</p>
        ) : (
          <div className="rounded-xl border border-red-100 bg-white overflow-hidden shadow-sm">
            <table className="w-full text-sm">
              <thead className="bg-red-50 text-red-700">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">Nome</th>
                  <th className="px-4 py-3 text-left font-medium">Frequência</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.lowAttendanceStudents.map((student) => (
                  <tr key={student.id} className="hover:bg-red-50/40">
                    <td className="px-4 py-3 font-medium text-slate-800">{student.fullName}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
                        ⚠️ {student.attendanceRate != null ? `${student.attendanceRate}%` : '—'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Pending roll calls */}
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
          Turmas com Chamada Pendente Hoje
        </h2>
        {data.classesWithPendingRollCall.length === 0 ? (
          <p className="text-slate-500 text-sm">Todas as chamadas de hoje foram registradas! ✅</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {data.classesWithPendingRollCall.map((cls) => (
              <div
                key={cls.id}
                className="flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 px-4 py-3"
              >
                <div>
                  <p className="font-medium text-slate-800">{cls.name}</p>
                  <p className="text-xs text-slate-500">{cls.studentCount} alunos</p>
                </div>
                <span className="text-xs rounded-full bg-amber-200 text-amber-800 px-2 py-0.5 font-semibold">
                  Pendente
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
