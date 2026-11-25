import type {
  AttendanceStatus,
  CalendarDayKind,
  EnrollmentStatus,
  Relationship,
  Role,
  Shift,
} from '@/shared/api/types'

export const shiftLabels: Record<Shift, string> = {
  morning: 'Manhã',
  afternoon: 'Tarde',
  evening: 'Noite',
}

export const roleLabels: Record<Role, string> = {
  admin: 'Administração',
  teacher: 'Professor(a)',
}

export const attendanceLabels: Record<AttendanceStatus, string> = {
  present: 'Presente',
  absent: 'Ausente',
}

export const relationshipLabels: Record<Relationship, string> = {
  mother: 'Mãe',
  father: 'Pai',
  grandparent: 'Avó/Avô',
  sibling: 'Irmã(o)',
  uncle_aunt: 'Tia/Tio',
  legal_guardian: 'Responsável legal',
  other: 'Outro',
}

export const calendarDayKindLabels: Record<CalendarDayKind, string> = {
  holiday: 'Feriado',
  recess: 'Recesso',
  non_school_day: 'Dia não letivo',
  extra_school_day: 'Dia letivo extra',
}

export const enrollmentStatusLabels: Record<EnrollmentStatus, string> = {
  active: 'Ativa',
  transferred: 'Transferida',
  cancelled: 'Cancelada',
  completed: 'Concluída',
}

export function optionsFrom<T extends string>(labels: Record<T, string>) {
  return (Object.entries(labels) as [T, string][]).map(([value, label]) => ({ value, label }))
}
