import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { useClasses } from '@/features/classes/api/classes.queries'
import { useStudents } from '@/features/students/api/students.queries'
import { useRollCalls, useSaveRollCall } from '@/features/roll-call/api/roll-call.queries'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/lib/api'
import type { Subject, AttendanceStatus } from '@/shared/types'

interface StudentAttendance {
  studentId: string
  status: AttendanceStatus | 'unmarked'
}

export default function RollCallPage() {
  const today = format(new Date(), 'yyyy-MM-dd')

  const [selectedClass,   setSelectedClass]   = useState('')
  const [selectedSubject, setSelectedSubject] = useState('')
  const [selectedDate,    setSelectedDate]    = useState(today)
  const [attendance,      setAttendance]      = useState<StudentAttendance[]>([])
  const [savedOk,         setSavedOk]         = useState(false)

  const { data: classesData } = useClasses()
  const classes = classesData?.items ?? []

  // Subjects: fetched from backend
  const { data: subjectsData } = useQuery({
    queryKey: ['subjects'],
    queryFn: () => api.get<{ items: Subject[]; total: number }>('/subjects').catch(() => ({ items: [], total: 0 })),
    staleTime: 10 * 60 * 1000,
  })
  const subjects = subjectsData?.items ?? []

  // Initialize selections when data loads
  useEffect(() => {
    if (classes.length > 0 && !selectedClass) setSelectedClass(classes[0].id)
  }, [classes, selectedClass])

  useEffect(() => {
    if (subjects.length > 0 && !selectedSubject) setSelectedSubject(subjects[0].id)
  }, [subjects, selectedSubject])

  // Students of selected class
  const { data: studentsData } = useStudents({ classId: selectedClass || undefined })
  const classStudents = studentsData?.items ?? []

  // Existing roll call for this class+date
  const { data: rollCallsData } = useRollCalls({
    classId: selectedClass || undefined,
    date:    selectedDate,
  })

  // Pre-fill attendance from existing roll call
  useEffect(() => {
    const existing = rollCallsData?.items[0]
    if (existing) {
      setAttendance(
        existing.attendances.map((a) => ({ studentId: a.studentId, status: a.status })),
      )
    } else {
      setAttendance([])
    }
    setSavedOk(false)
  }, [rollCallsData, selectedClass, selectedDate])

  const saveRollCall = useSaveRollCall()

  function getStatus(studentId: string): AttendanceStatus | 'unmarked' {
    return attendance.find((a) => a.studentId === studentId)?.status ?? 'unmarked'
  }

  function setStatus(studentId: string, status: AttendanceStatus) {
    setSavedOk(false)
    setAttendance((prev) => {
      const existing = prev.find((a) => a.studentId === studentId)
      if (existing) return prev.map((a) => (a.studentId === studentId ? { ...a, status } : a))
      return [...prev, { studentId, status }]
    })
  }

  function markAllPresent() {
    setSavedOk(false)
    setAttendance(classStudents.map((s) => ({ studentId: s.id, status: 'present' as const })))
  }

  function handleClassChange(classId: string) {
    setSelectedClass(classId)
    setAttendance([])
    setSavedOk(false)
  }

  const presentCount  = classStudents.filter((s) => getStatus(s.id) === 'present').length
  const absentCount   = classStudents.filter((s) => getStatus(s.id) === 'absent').length
  const unmarkedCount = classStudents.filter((s) => getStatus(s.id) === 'unmarked').length
  const canSave       = unmarkedCount === 0 && classStudents.length > 0

  function handleSave() {
    if (!canSave || !selectedClass || !selectedSubject) return
    const marked = attendance.filter((a): a is { studentId: string; status: AttendanceStatus } =>
      a.status === 'present' || a.status === 'absent',
    )
    saveRollCall.mutate(
      {
        classId:    selectedClass,
        subjectId:  selectedSubject,
        lessonDate: selectedDate,
        attendances: marked,
      },
      {
        onSuccess: () => setSavedOk(true),
      },
    )
  }

  const selectedClassName = classes.find((c) => c.id === selectedClass)?.name ?? ''

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Chamada</h1>

      <div className="flex flex-wrap gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-500">Turma</label>
          <select
            value={selectedClass}
            onChange={(e) => handleClassChange(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-500">Disciplina</label>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            {subjects.length === 0
              ? <option value="">Carregando...</option>
              : subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))
            }
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-slate-500">Data</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => { setSelectedDate(e.target.value); setSavedOk(false) }}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-4 rounded-xl bg-slate-100 px-5 py-3 text-sm font-medium">
        <span className="text-green-700">✓ {presentCount} presentes</span>
        <span className="text-red-600">✗ {absentCount} ausentes</span>
        {unmarkedCount > 0 && (
          <span className="text-slate-500">○ {unmarkedCount} não marcados</span>
        )}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
          <p className="text-sm font-medium text-slate-700">{selectedClassName}</p>
          <button
            onClick={markAllPresent}
            className="text-xs rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50 transition-colors text-slate-600"
          >
            Marcar todos presentes
          </button>
        </div>
        {classStudents.length === 0 ? (
          <p className="px-4 py-6 text-sm text-slate-400 text-center">
            {selectedClass ? 'Carregando alunos...' : 'Selecione uma turma.'}
          </p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {classStudents.map((student) => {
              const status = getStatus(student.id)
              return (
                <li key={student.id} className="flex items-center justify-between px-4 py-3">
                  <span className="font-medium text-slate-800 text-sm">{student.fullName}</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setStatus(student.id, 'present')}
                      className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                        status === 'present'
                          ? 'bg-green-600 text-white'
                          : 'border border-green-300 text-green-700 hover:bg-green-50'
                      }`}
                    >
                      Presente
                    </button>
                    <button
                      onClick={() => setStatus(student.id, 'absent')}
                      className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${
                        status === 'absent'
                          ? 'bg-red-600 text-white'
                          : 'border border-red-300 text-red-700 hover:bg-red-50'
                      }`}
                    >
                      Ausente
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={handleSave}
          disabled={!canSave || saveRollCall.isPending}
          className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {saveRollCall.isPending ? 'Salvando...' : 'Salvar Chamada'}
        </button>
        {!canSave && classStudents.length > 0 && (
          <p className="text-xs text-slate-500">Marque todos os alunos para salvar.</p>
        )}
        {saveRollCall.isError && (
          <p className="text-xs text-red-600">Erro ao salvar. Tente novamente.</p>
        )}
        {savedOk && (
          <p className="text-sm font-medium text-green-600">✓ Chamada salva com sucesso!</p>
        )}
      </div>
    </div>
  )
}