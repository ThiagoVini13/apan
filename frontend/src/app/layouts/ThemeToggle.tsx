import { useId } from 'react'
import { cn } from '@/shared/lib/cn'
import { MonitorIcon, MoonIcon, SunIcon } from '@/shared/ui/icons'
import { useThemeStore, type ThemeChoice } from '@/stores/theme.store'

const options: { value: ThemeChoice; label: string; icon: typeof SunIcon }[] = [
  { value: 'light', label: 'Claro', icon: SunIcon },
  { value: 'dark', label: 'Escuro', icon: MoonIcon },
  { value: 'system', label: 'Sistema', icon: MonitorIcon },
]

export function ThemeToggle() {
  const theme = useThemeStore((state) => state.theme)
  const setTheme = useThemeStore((state) => state.setTheme)
  const name = useId()

  return (
    <fieldset className="flex flex-col gap-1">
      <legend className="mb-1 text-xs font-semibold text-fg-muted">Tema</legend>
      <div className="flex rounded-lg border border-line-strong p-0.5">
        {options.map(({ value, label, icon: Icon }) => (
          <label
            key={value}
            className={cn(
              'flex min-h-11 flex-1 cursor-pointer items-center justify-center gap-1.5 rounded-md px-2 text-xs font-medium has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-focus-ring',
              theme === value ? 'bg-primary text-primary-fg' : 'text-fg hover:bg-surface-muted',
            )}
          >
            <input
              type="radio"
              name={name}
              value={value}
              checked={theme === value}
              onChange={() => setTheme(value)}
              className="sr-only"
            />
            <Icon className="size-4" />
            {label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}
