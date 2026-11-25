import { useState } from 'react'
import { useSubjectOptions } from '@/shared/api/reference'
import type { Subject } from '@/shared/api/types'
import { useDocumentTitle } from '@/shared/hooks/useDocumentTitle'
import { cn } from '@/shared/lib/cn'
import { Button } from '@/shared/ui/Button'
import { ConfirmDialog } from '@/shared/ui/Dialog'
import { PencilIcon, PlusIcon, TrashIcon } from '@/shared/ui/icons'
import { PageHeader, TableContainer } from '@/shared/ui/Layout'
import { tableClasses } from '@/shared/ui/table'
import { EmptyState, ErrorState, LoadingList } from '@/shared/ui/States'
import { notify } from '@/shared/ui/toast.store'
import { useDeleteSubject } from '../api/subjects.queries'
import { SubjectDialog } from '../components/SubjectDialog'

export default function SubjectsPage() {
  useDocumentTitle('Disciplinas')
  const subjects = useSubjectOptions()
  const remove = useDeleteSubject()
  const [editing, setEditing] = useState<Subject | null | 'new'>(null)
  const [deleting, setDeleting] = useState<Subject | null>(null)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Disciplinas"
        actions={
          <Button onClick={() => setEditing('new')}>
            <PlusIcon className="size-4" />
            Nova disciplina
          </Button>
        }
      />
      {subjects.isPending && <LoadingList label="Carregando disciplinas…" />}
      {subjects.isError && <ErrorState error={subjects.error} onRetry={() => subjects.refetch()} />}
      {subjects.data?.length === 0 && <EmptyState title="Nenhuma disciplina cadastrada" />}
      {subjects.data && subjects.data.length > 0 && (
        <TableContainer label="Lista de disciplinas">
          <table className={tableClasses.table}>
            <thead className={tableClasses.head}>
              <tr>
                <th scope="col" className={tableClasses.th}>
                  Nome
                </th>
                <th scope="col" className={tableClasses.th}>
                  Código
                </th>
                <th scope="col" className={tableClasses.th}>
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {subjects.data.map((subject) => (
                <tr key={subject.id} className={tableClasses.row}>
                  <th scope="row" className={cn(tableClasses.td, 'font-medium')}>
                    {subject.name}
                  </th>
                  <td className={tableClasses.td}>{subject.code}</td>
                  <td className={cn(tableClasses.td, 'whitespace-nowrap text-right')}>
                    <Button
                      variant="ghost"
                      aria-label={`Editar ${subject.name}`}
                      onClick={() => setEditing(subject)}
                    >
                      <PencilIcon className="size-4" />
                      Editar
                    </Button>
                    <Button
                      variant="ghost"
                      aria-label={`Excluir ${subject.name}`}
                      onClick={() => setDeleting(subject)}
                    >
                      <TrashIcon className="size-4" />
                      Excluir
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableContainer>
      )}
      {editing && (
        <SubjectDialog
          subject={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={`Excluir ${deleting?.name ?? ''}?`}
        description="Só é possível excluir disciplinas que ainda não foram usadas em turmas ou chamadas."
        confirmLabel="Excluir"
        tone="danger"
        isPending={remove.isPending}
        onConfirm={() =>
          deleting &&
          remove.mutate(deleting.id, {
            onSuccess: () => notify.success('Disciplina excluída.'),
            onSettled: () => setDeleting(null),
          })
        }
      />
    </div>
  )
}
