import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import type { SchoolYear } from '@/shared/api/types'
import { applyApiErrors } from '@/shared/lib/form'
import { formatDate } from '@/shared/lib/format'
import { calendarDayKindLabels, optionsFrom } from '@/shared/lib/labels'
import { Button } from '@/shared/ui/Button'
import { Dialog } from '@/shared/ui/Dialog'
import { Field, Input, Select } from '@/shared/ui/Field'
import { FormErrorSummary } from '@/shared/ui/FormErrorSummary'
import { PlusIcon, TrashIcon } from '@/shared/ui/icons'
import { LoadingList } from '@/shared/ui/States'
import { notify } from '@/shared/ui/toast.store'
import {
  useAddCalendarDay,
  useAddTerm,
  useCalendarDays,
  useDeleteCalendarDay,
  useDeleteTerm,
  useTermsOf,
} from '../api/school-years.queries'
import {
  CalendarDaySchema,
  TermSchema,
  type CalendarDayForm,
  type TermForm,
} from '../schemas/school-year.schema'

export function CalendarDialog({ year, onClose }: { year: SchoolYear; onClose: () => void }) {
  return (
    <Dialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={`Calendário de ${year.name}`}
      description={`De ${formatDate(year.startsOn)} a ${formatDate(year.endsOn)}. Fins de semana já contam como dias não letivos.`}
      size="lg"
    >
      <div className="flex flex-col gap-8">
        <TermsSection year={year} />
        <DaysSection year={year} />
      </div>
    </Dialog>
  )
}

function TermsSection({ year }: { year: SchoolYear }) {
  const terms = useTermsOf(year.id)
  const add = useAddTerm(year.id)
  const remove = useDeleteTerm(year.id)
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<TermForm>({
    resolver: zodResolver(TermSchema),
    mode: 'onTouched',
    defaultValues: { name: '', startsOn: '', endsOn: '' },
  })

  const onSubmit = handleSubmit((data) => {
    setSummary(null)
    add.mutate(data, {
      onSuccess: () => {
        reset()
        notify.success('Período adicionado.')
      },
      onError: (error) =>
        setSummary(applyApiErrors(error, setError, ['name', 'startsOn', 'endsOn'])),
    })
  })

  return (
    <section aria-labelledby="terms-heading" className="flex flex-col gap-3">
      <h3 id="terms-heading" className="font-semibold text-fg">
        Bimestres e outros períodos
      </h3>
      {terms.isPending && <LoadingList label="Carregando períodos…" rows={2} />}
      <ul className="flex flex-col gap-2">
        {terms.data?.map((term) => (
          <li
            key={term.id}
            className="flex items-center justify-between gap-2 rounded-lg border border-line px-3 py-2"
          >
            <span className="text-fg">
              <span className="font-medium">{term.name}</span>{' '}
              <span className="text-sm text-fg-muted">
                {formatDate(term.startsOn)} a {formatDate(term.endsOn)}
              </span>
            </span>
            <Button
              variant="ghost"
              aria-label={`Excluir ${term.name}`}
              onClick={() => remove.mutate(term.id)}
            >
              <TrashIcon className="size-4" />
            </Button>
          </li>
        ))}
      </ul>
      <form
        onSubmit={onSubmit}
        noValidate
        className="grid gap-3 rounded-lg border border-line p-3 sm:grid-cols-[1fr_1fr_1fr_auto] sm:items-end"
      >
        <div className="sm:col-span-4">
          <FormErrorSummary message={summary} />
        </div>
        <Field label="Nome do período" error={errors.name?.message}>
          {(props) => <Input {...props} placeholder="1º bimestre" {...register('name')} />}
        </Field>
        <Field label="Início" error={errors.startsOn?.message}>
          {(props) => (
            <Input
              {...props}
              type="date"
              min={year.startsOn}
              max={year.endsOn}
              {...register('startsOn')}
            />
          )}
        </Field>
        <Field label="Término" error={errors.endsOn?.message}>
          {(props) => (
            <Input
              {...props}
              type="date"
              min={year.startsOn}
              max={year.endsOn}
              {...register('endsOn')}
            />
          )}
        </Field>
        <Button type="submit" variant="secondary" isPending={add.isPending}>
          <PlusIcon className="size-4" />
          Adicionar
        </Button>
      </form>
    </section>
  )
}

function DaysSection({ year }: { year: SchoolYear }) {
  const days = useCalendarDays(year.id)
  const add = useAddCalendarDay(year.id)
  const remove = useDeleteCalendarDay(year.id)
  const [summary, setSummary] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<CalendarDayForm>({
    resolver: zodResolver(CalendarDaySchema),
    mode: 'onTouched',
    defaultValues: { day: '', kind: 'holiday', description: '' },
  })

  const onSubmit = handleSubmit((data) => {
    setSummary(null)
    add.mutate(
      { ...data, description: data.description || null },
      {
        onSuccess: () => {
          reset()
          notify.success('Dia adicionado ao calendário.')
        },
        onError: (error) =>
          setSummary(applyApiErrors(error, setError, ['day', 'kind', 'description'])),
      },
    )
  })

  return (
    <section aria-labelledby="days-heading" className="flex flex-col gap-3">
      <h3 id="days-heading" className="font-semibold text-fg">
        Feriados, recessos e dias letivos extras
      </h3>
      {days.isPending && <LoadingList label="Carregando calendário…" rows={2} />}
      {days.data?.length === 0 && (
        <p className="text-sm text-fg-muted">Nenhum dia especial cadastrado.</p>
      )}
      <ul className="flex flex-col gap-2">
        {days.data?.map((day) => (
          <li
            key={day.id}
            className="flex items-center justify-between gap-2 rounded-lg border border-line px-3 py-2"
          >
            <span className="text-fg">
              <span className="font-medium tabular-nums">{formatDate(day.day)}</span>{' '}
              <span className="text-sm text-fg-muted">
                {calendarDayKindLabels[day.kind]}
                {day.description ? ` · ${day.description}` : ''}
              </span>
            </span>
            <Button
              variant="ghost"
              aria-label={`Excluir ${formatDate(day.day)}`}
              onClick={() => remove.mutate(day.id)}
            >
              <TrashIcon className="size-4" />
            </Button>
          </li>
        ))}
      </ul>
      <form
        onSubmit={onSubmit}
        noValidate
        className="grid gap-3 rounded-lg border border-line p-3 sm:grid-cols-[1fr_1fr_1fr_auto] sm:items-end"
      >
        <div className="sm:col-span-4">
          <FormErrorSummary message={summary} />
        </div>
        <Field label="Dia" error={errors.day?.message}>
          {(props) => (
            <Input
              {...props}
              type="date"
              min={year.startsOn}
              max={year.endsOn}
              {...register('day')}
            />
          )}
        </Field>
        <Field label="Tipo" error={errors.kind?.message}>
          {(props) => (
            <Select {...props} {...register('kind')}>
              {optionsFrom(calendarDayKindLabels).map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Descrição (opcional)" error={errors.description?.message}>
          {(props) => <Input {...props} placeholder="Tiradentes" {...register('description')} />}
        </Field>
        <Button type="submit" variant="secondary" isPending={add.isPending}>
          <PlusIcon className="size-4" />
          Adicionar
        </Button>
      </form>
    </section>
  )
}
