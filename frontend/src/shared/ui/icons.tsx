import type { ComponentPropsWithoutRef } from 'react'
import { cn } from '@/shared/lib/cn'

type IconProps = ComponentPropsWithoutRef<'svg'>

function createIcon(paths: string[], name: string) {
  function Icon({ className, ...props }: IconProps) {
    return (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        focusable="false"
        className={cn('size-5 shrink-0', className)}
        {...props}
      >
        {paths.map((d) => (
          <path key={d} d={d} />
        ))}
      </svg>
    )
  }
  Icon.displayName = name
  return Icon
}

export const CheckIcon = createIcon(['M5 12.5l4.5 4.5L19 7.5'], 'CheckIcon')
export const XIcon = createIcon(['M6 6l12 12', 'M18 6L6 18'], 'XIcon')
export const AlertIcon = createIcon(
  ['M12 3l9.5 16.5h-19L12 3z', 'M12 10v4', 'M12 17.5h.01'],
  'AlertIcon',
)
export const InfoIcon = createIcon(
  ['M12 21a9 9 0 100-18 9 9 0 000 18z', 'M12 11v5', 'M12 8h.01'],
  'InfoIcon',
)
export const HomeIcon = createIcon(['M3 11l9-7 9 7', 'M5 10v10h14V10', 'M10 20v-6h4v6'], 'HomeIcon')
export const ClipboardIcon = createIcon(
  ['M9 4h6v3H9z', 'M8 5H6v15h12V5h-2', 'M9 12l2 2 4-4', 'M9 17h6'],
  'ClipboardIcon',
)
export const UsersIcon = createIcon(
  [
    'M9 11a4 4 0 100-8 4 4 0 000 8z',
    'M2 21v-1a6 6 0 0112 0v1',
    'M16 3.5a4 4 0 010 7',
    'M22 21v-1a6 6 0 00-4-5.6',
  ],
  'UsersIcon',
)
export const ChartIcon = createIcon(
  ['M4 20V4', 'M4 20h16', 'M8 16v-5', 'M12 16V8', 'M16 16v-3'],
  'ChartIcon',
)
export const SettingsIcon = createIcon(
  [
    'M12 15a3 3 0 100-6 3 3 0 000 6z',
    'M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z',
  ],
  'SettingsIcon',
)
export const LogOutIcon = createIcon(['M9 21H5V3h4', 'M16 17l5-5-5-5', 'M21 12H9'], 'LogOutIcon')
export const PlusIcon = createIcon(['M12 5v14', 'M5 12h14'], 'PlusIcon')
export const PencilIcon = createIcon(['M4 20h4L19 9l-4-4L4 16v4z', 'M13.5 6.5l4 4'], 'PencilIcon')
export const SearchIcon = createIcon(
  ['M11 18a7 7 0 100-14 7 7 0 000 14z', 'M20 20l-4-4'],
  'SearchIcon',
)
export const DownloadIcon = createIcon(['M12 4v11', 'M7 10l5 5 5-5', 'M5 20h14'], 'DownloadIcon')
export const ChevronLeftIcon = createIcon(['M15 6l-6 6 6 6'], 'ChevronLeftIcon')
export const ChevronRightIcon = createIcon(['M9 6l6 6-6 6'], 'ChevronRightIcon')
export const CalendarIcon = createIcon(
  ['M4 6h16v14H4z', 'M4 10h16', 'M8 3v5', 'M16 3v5'],
  'CalendarIcon',
)
export const ShieldIcon = createIcon(
  ['M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6l8-3z'],
  'ShieldIcon',
)
export const BookIcon = createIcon(
  ['M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2V5z', 'M4 19a2 2 0 012-2h13'],
  'BookIcon',
)
export const SchoolIcon = createIcon(
  ['M3 9l9-5 9 5-9 5-9-5z', 'M7 11.5V16c0 1.5 2.2 3 5 3s5-1.5 5-3v-4.5'],
  'SchoolIcon',
)
export const ArchiveIcon = createIcon(['M3 5h18v4H3z', 'M5 9v10h14V9', 'M10 13h4'], 'ArchiveIcon')
export const TrashIcon = createIcon(['M4 7h16', 'M9 7V4h6v3', 'M6 7l1 13h10l1-13'], 'TrashIcon')
export const StarIcon = createIcon(
  ['M12 3l2.8 5.7 6.2.9-4.5 4.4 1 6.2L12 17.3 6.5 20.2l1-6.2L3 9.6l6.2-.9L12 3z'],
  'StarIcon',
)
export const SunIcon = createIcon(
  [
    'M12 17a5 5 0 100-10 5 5 0 000 10z',
    'M12 1v2',
    'M12 21v2',
    'M4.2 4.2l1.4 1.4',
    'M18.4 18.4l1.4 1.4',
    'M1 12h2',
    'M21 12h2',
    'M4.2 19.8l1.4-1.4',
    'M18.4 5.6l1.4-1.4',
  ],
  'SunIcon',
)
export const MoonIcon = createIcon(['M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z'], 'MoonIcon')
export const MonitorIcon = createIcon(['M3 4h18v12H3z', 'M8 20h8', 'M12 16v4'], 'MonitorIcon')
export const HistoryIcon = createIcon(
  ['M3 12a9 9 0 103-6.7L3 8', 'M3 3v5h5', 'M12 7v5l3 3'],
  'HistoryIcon',
)
export const KeyIcon = createIcon(
  ['M15 7a4 4 0 11-3.9 4.9L4 19v2h3v-2h2v-2h2l1.1-1.1A4 4 0 0115 7z'],
  'KeyIcon',
)
export const SpinnerIcon = createIcon(['M12 3a9 9 0 109 9'], 'SpinnerIcon')
