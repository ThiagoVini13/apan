export const MOCK_CLASSES = [
  { id: 'c1', name: '5º Ano A', shift: 'morning' as const, grade: '5', studentCount: 5 },
  { id: 'c2', name: '6º Ano B', shift: 'afternoon' as const, grade: '6', studentCount: 5 },
  { id: 'c3', name: '7º Ano C', shift: 'morning' as const, grade: '7', studentCount: 5 },
]

export const MOCK_STUDENTS = [
  { id: 's1',  classId: 'c1', enrollmentNumber: '2024001', fullName: 'Ana Beatriz Souza',       birthDate: '2014-03-15', attendanceRate: 92 },
  { id: 's2',  classId: 'c1', enrollmentNumber: '2024002', fullName: 'Bruno Carvalho Lima',      birthDate: '2014-07-22', attendanceRate: 85 },
  { id: 's3',  classId: 'c1', enrollmentNumber: '2024003', fullName: 'Carla Dias Ferreira',      birthDate: '2014-01-10', attendanceRate: 70 },
  { id: 's4',  classId: 'c1', enrollmentNumber: '2024004', fullName: 'Diego Mendes Costa',       birthDate: '2014-11-30', attendanceRate: 95 },
  { id: 's5',  classId: 'c1', enrollmentNumber: '2024005', fullName: 'Eduarda Pires Santos',     birthDate: '2014-05-08', attendanceRate: 78 },
  { id: 's6',  classId: 'c2', enrollmentNumber: '2024006', fullName: 'Felipe Rocha Alves',       birthDate: '2013-09-12', attendanceRate: 88 },
  { id: 's7',  classId: 'c2', enrollmentNumber: '2024007', fullName: 'Gabriela Nunes Teixeira',  birthDate: '2013-04-25', attendanceRate: 62 },
  { id: 's8',  classId: 'c2', enrollmentNumber: '2024008', fullName: 'Henrique Barbosa Gomes',   birthDate: '2013-12-03', attendanceRate: 91 },
  { id: 's9',  classId: 'c2', enrollmentNumber: '2024009', fullName: 'Isabela Castro Ribeiro',   birthDate: '2013-06-18', attendanceRate: 76 },
  { id: 's10', classId: 'c2', enrollmentNumber: '2024010', fullName: 'João Victor Lopes',        birthDate: '2013-08-07', attendanceRate: 83 },
  { id: 's11', classId: 'c3', enrollmentNumber: '2024011', fullName: 'Kamila Oliveira Faria',    birthDate: '2012-02-14', attendanceRate: 97 },
  { id: 's12', classId: 'c3', enrollmentNumber: '2024012', fullName: 'Lucas Pereira Monteiro',   birthDate: '2012-10-29', attendanceRate: 58 },
  { id: 's13', classId: 'c3', enrollmentNumber: '2024013', fullName: 'Marina Azevedo Cunha',     birthDate: '2012-07-11', attendanceRate: 89 },
  { id: 's14', classId: 'c3', enrollmentNumber: '2024014', fullName: 'Nicolas Borges Ramos',     birthDate: '2012-03-22', attendanceRate: 74 },
  { id: 's15', classId: 'c3', enrollmentNumber: '2024015', fullName: 'Olivia Correia Vieira',    birthDate: '2012-11-05', attendanceRate: 81 },
]

export const MOCK_SUBJECTS = [
  { id: 'sub1', name: 'Matemática', code: 'MATH' },
  { id: 'sub2', name: 'Português',  code: 'PORT' },
]

export type MockClass   = typeof MOCK_CLASSES[number]
export type MockStudent = typeof MOCK_STUDENTS[number]
export type MockSubject = typeof MOCK_SUBJECTS[number]
