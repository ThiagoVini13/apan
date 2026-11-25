import { ApiError } from './http'

const messages: Record<string, string> = {
  network_error: 'Sem conexão com o servidor. Verifique a internet e tente novamente.',
  internal_error: 'Ocorreu um erro inesperado. Tente novamente em instantes.',
  rate_limited: 'Muitas tentativas seguidas. Aguarde um pouco e tente de novo.',
  not_authenticated: 'Sua sessão expirou. Entre novamente.',
  invalid_token: 'Sua sessão expirou. Entre novamente.',
  permission_denied: 'Você não tem permissão para esta ação.',
  password_change_required: 'Defina uma nova senha para continuar.',
  csrf_failed: 'Não foi possível validar a sessão. Recarregue a página.',
  invalid_credentials: 'E-mail ou senha incorretos.',
  account_locked: 'Conta bloqueada temporariamente por muitas tentativas. Tente mais tarde.',
  invalid_reset_token: 'Este link expirou ou já foi usado. Peça um novo.',
  invalid_current_password: 'A senha atual está incorreta.',
  weak_password: 'A nova senha não atende aos requisitos.',
  password_too_short: 'Use pelo menos 10 caracteres.',
  password_too_long: 'Use no máximo 128 caracteres.',
  password_too_common: 'Essa senha é muito comum. Escolha outra.',
  password_contains_email: 'A senha não pode conter o seu e-mail.',
  password_unchanged: 'A nova senha deve ser diferente da atual.',
  email_taken: 'Já existe uma conta com este e-mail.',
  last_admin: 'Precisa existir ao menos uma conta de administração ativa.',
  cannot_deactivate_self: 'Você não pode desativar a sua própria conta.',
  user_not_found: 'Usuário não encontrado.',
  school_year_not_found: 'Ano letivo não encontrado.',
  school_year_name_taken: 'Já existe um ano letivo com esse nome.',
  school_year_in_use: 'Este ano letivo tem turmas e não pode ser excluído.',
  terms_outside_school_year: 'Há bimestres fora das novas datas do ano letivo.',
  term_name_taken: 'Já existe um período com esse nome.',
  term_overlaps: 'O período se sobrepõe a outro já cadastrado.',
  calendar_day_taken: 'Esse dia já está no calendário.',
  date_outside_school_year: 'A data está fora do ano letivo.',
  invalid_date_range: 'A data final deve ser igual ou posterior à inicial.',
  date_range_too_long: 'Escolha um período de até 400 dias.',
  subject_not_found: 'Disciplina não encontrada.',
  subject_code_taken: 'Já existe uma disciplina com esse código.',
  subject_in_use: 'Esta disciplina está em uso e não pode ser excluída.',
  class_not_found: 'Turma não encontrada.',
  class_name_taken: 'Já existe uma turma com esse nome neste turno.',
  class_archived: 'Esta turma está arquivada.',
  class_capacity_exceeded: 'A turma já atingiu a capacidade.',
  capacity_below_enrollments:
    'A capacidade não pode ser menor que o número de alunos matriculados.',
  invalid_subject_teachers: 'Revise as disciplinas e os professores informados.',
  duplicate_subject: 'Disciplina repetida.',
  teacher_not_found: 'Escolha um(a) professor(a) ativo(a).',
  student_not_found: 'Aluno não encontrado.',
  student_archived: 'Este aluno está arquivado.',
  student_too_young: 'O aluno precisa ter pelo menos 3 anos.',
  date_in_future: 'A data não pode ser futura.',
  invalid_birth_date: 'Data de nascimento inválida.',
  guardian_required: 'Alunos menores de 18 anos precisam de um responsável.',
  primary_guardian_required: 'Escolha outro responsável principal antes de desmarcar este.',
  multiple_primary_guardians: 'Marque apenas um responsável principal.',
  guardian_not_found: 'Responsável não encontrado.',
  invalid_phone: 'Informe DDD e número, por exemplo (92) 99123-4567.',
  class_required: 'Escolha a turma do aluno.',
  student_already_enrolled: 'O aluno já tem matrícula ativa neste ano letivo.',
  enrollment_not_active: 'Esta matrícula não está mais ativa.',
  same_class: 'Escolha uma turma diferente da atual.',
  different_school_year: 'A turma de destino é de outro ano letivo.',
  transfer_before_start: 'A transferência deve ser depois do início da matrícula.',
  lesson_in_future: 'Não é possível registrar chamada de uma data futura.',
  not_a_school_day: 'Esta data não é dia letivo no calendário.',
  roll_call_locked: 'O prazo para editar esta chamada terminou. Fale com a coordenação.',
  roll_call_incomplete: 'Marque todos os alunos antes de salvar.',
  student_not_enrolled: 'A lista de alunos mudou. Recarregue a chamada.',
  duplicate_student: 'A lista de alunos tem itens repetidos. Recarregue a chamada.',
  subject_not_assigned: 'Você não leciona esta disciplina nesta turma.',
  roll_call_not_found: 'Chamada não encontrada.',
  conflict: 'Os dados mudaram enquanto você editava. Recarregue e tente de novo.',
  validation_error: 'Revise os campos destacados.',
}

export function messageForCode(code: string): string {
  return messages[code] ?? 'Não foi possível concluir a ação. Tente novamente.'
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return messageForCode(error.code)
  return messageForCode('internal_error')
}

export function fieldErrorMessage(code: string): string {
  return messages[code] ?? 'Valor inválido.'
}
