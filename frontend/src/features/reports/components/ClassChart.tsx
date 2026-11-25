import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from 'recharts'
import type { ClassReportRow } from '@/shared/api/types'
import { MIN_ATTENDANCE_RATE } from '@/shared/lib/constants'
import { formatPercent } from '@/shared/lib/format'
import { AttendanceRateBadge } from '@/shared/ui/Badge'
import { TableContainer } from '@/shared/ui/Layout'
import { tableClasses } from '@/shared/ui/table'

export function ClassChart({ rows }: { rows: ClassReportRow[] }) {
  const data = rows.map((row) => ({ name: row.className, rate: row.attendanceRate ?? 0 }))
  const description = rows
    .map((row) => `${row.className}: ${formatPercent(row.attendanceRate)}`)
    .join('; ')

  return (
    <div className="flex flex-col gap-4">
      <figure className="h-64 w-full" role="img" aria-label={`Presença por turma. ${description}`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 24, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--line)" />
            <XAxis
              dataKey="name"
              tick={{ fill: 'var(--fg-muted)', fontSize: 12 }}
              stroke="var(--line-strong)"
            />
            <YAxis
              domain={[0, 100]}
              tickFormatter={(value: number) => `${value}%`}
              tick={{ fill: 'var(--fg-muted)', fontSize: 12 }}
              stroke="var(--line-strong)"
              width={44}
            />
            <ReferenceLine
              y={MIN_ATTENDANCE_RATE}
              stroke="var(--danger)"
              strokeDasharray="4 4"
              label={{
                value: 'Mínimo 75%',
                fill: 'var(--danger)',
                fontSize: 12,
                position: 'insideTopRight',
              }}
            />
            <Bar
              dataKey="rate"
              fill="var(--chart-1)"
              radius={[6, 6, 0, 0]}
              isAnimationActive={false}
            >
              <LabelList
                dataKey="rate"
                position="top"
                formatter={(value: unknown) => formatPercent(Number(value))}
                fill="var(--fg)"
                fontSize={12}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </figure>

      <TableContainer label="Tabela de presença por turma">
        <table className={tableClasses.table}>
          <thead className={tableClasses.head}>
            <tr>
              <th scope="col" className={tableClasses.th}>
                Turma
              </th>
              <th scope="col" className={tableClasses.th}>
                Aulas
              </th>
              <th scope="col" className={tableClasses.th}>
                Alunos
              </th>
              <th scope="col" className={tableClasses.th}>
                Presenças
              </th>
              <th scope="col" className={tableClasses.th}>
                Faltas
              </th>
              <th scope="col" className={tableClasses.th}>
                Frequência
              </th>
              <th scope="col" className={tableClasses.th}>
                Abaixo de 75%
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.classId} className={tableClasses.row}>
                <th scope="row" className={`${tableClasses.td} font-medium`}>
                  {row.className}
                </th>
                <td className={`${tableClasses.td} tabular-nums`}>{row.lessons}</td>
                <td className={`${tableClasses.td} tabular-nums`}>{row.students}</td>
                <td className={`${tableClasses.td} tabular-nums`}>{row.present}</td>
                <td className={`${tableClasses.td} tabular-nums`}>{row.absent}</td>
                <td className={tableClasses.td}>
                  <AttendanceRateBadge rate={row.attendanceRate} />
                </td>
                <td className={`${tableClasses.td} tabular-nums`}>{row.atRiskStudents}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableContainer>
    </div>
  )
}
