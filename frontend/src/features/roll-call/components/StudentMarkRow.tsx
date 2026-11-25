import type { AttendanceStatus, SheetStudent } from '@/shared/api/types'
import { cn } from '@/shared/lib/cn'
import { attendanceLabels } from '@/shared/lib/labels'
import { AlertIcon, CheckIcon, XIcon } from '@/shared/ui/icons'

type StudentMarkRowProps = {
  student: SheetStudent
  status: AttendanceStatus | null
  disabled: boolean
  onMark: (status: AttendanceStatus) => void
}

const OPTIONS: { value: AttendanceStatus; icon: typeof CheckIcon; activeClass: string }[] = [
  { value: 'present', icon: CheckIcon, activeClass: 'border-success bg-success-bg text-success' },
  { value: 'absent', icon: XIcon, activeClass: 'border-danger bg-danger-bg text-danger' },
]

export function StudentMarkRow({ student, status, disabled, onMark }: StudentMarkRowProps) {
  const groupLabel = `Situação de ${student.fullName}`
  return (
    <li
      data-student-id={student.studentId}
      className={cn(
        'flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3 last:border-0',
        status === null && !disabled && 'bg-warning-bg/40',
      )}
    >
      <div className="min-w-0">
        <p className="font-medium text-fg">{student.fullName}</p>
        <p className="text-sm text-fg-muted tabular-nums">Matrícula {student.enrollmentNumber}</p>
        {status === null && !disabled && (
          <p className="mt-0.5 flex items-center gap-1 text-sm font-medium text-warning">
            <AlertIcon className="size-4" />
            Sem marcação
          </p>
        )}
      </div>
      <div role="group" aria-label={groupLabel} className="flex gap-2">
        {OPTIONS.map(({ value, icon: Icon, activeClass }) => {
          const isActive = status === value
          return (
            <button
              key={value}
              type="button"
              aria-pressed={isActive}
              disabled={disabled}
              onClick={() => onMark(value)}
              className={cn(
                'flex min-h-11 min-w-28 items-center justify-center gap-1.5 rounded-lg border-2 px-3 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-60',
                isActive
                  ? activeClass
                  : 'border-line-strong bg-surface text-fg hover:bg-surface-muted',
              )}
            >
              <Icon className="size-4" />
              {attendanceLabels[value]}
            </button>
          )
        })}
      </div>
    </li>
  )
}
