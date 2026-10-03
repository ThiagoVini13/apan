interface StatusPillProps {
  rate: number
}

export function StatusPill({ rate }: StatusPillProps) {
  const isRisk = rate < 75
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${
        isRisk
          ? 'bg-red-100 text-red-700'
          : 'bg-green-100 text-green-700'
      }`}
    >
      {isRisk ? '⚠️' : '✓'} {rate}%
    </span>
  )
}
