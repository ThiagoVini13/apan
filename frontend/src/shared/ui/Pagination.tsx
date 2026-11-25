import { Button } from './Button'
import { ChevronLeftIcon, ChevronRightIcon } from './icons'

type PaginationProps = {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  if (pages <= 1) return null
  return (
    <nav aria-label="Paginação" className="flex items-center justify-between gap-2">
      <Button variant="secondary" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
        <ChevronLeftIcon />
        Anterior
      </Button>
      <p className="text-sm text-fg-muted tabular-nums">
        Página {page} de {pages}
      </p>
      <Button variant="secondary" disabled={page >= pages} onClick={() => onPageChange(page + 1)}>
        Próxima
        <ChevronRightIcon />
      </Button>
    </nav>
  )
}
