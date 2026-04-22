import { clsx } from 'clsx'

export function getConfidenceColorClass(score: number): string {
  if (score >= 80) return 'bg-confidence-critical text-white border-red-700/50'
  if (score >= 60) return 'bg-confidence-high text-white border-orange-700/50'
  if (score >= 40) return 'bg-confidence-medium text-amber-950 border-amber-500/50'
  if (score >= 20) return 'bg-confidence-low text-white border-green-700/50'
  return 'bg-confidence-minimal text-slate-900 border-slate-400/50'
}

export function getConfidenceTextColor(score: number): string {
  if (score >= 80) return 'text-confidence-critical'
  if (score >= 60) return 'text-confidence-high'
  if (score >= 40) return 'text-confidence-medium'
  if (score >= 20) return 'text-confidence-low'
  return 'text-confidence-minimal'
}

interface Props {
  score: number | undefined | null
  className?: string
}

export function ConfidenceBadge({ score, className }: Props) {
  if (score === undefined || score === null) return null

  const colorClass = getConfidenceColorClass(score)

  return (
    <span
      className={clsx(
        'inline-flex items-center justify-center px-2 py-0.5 rounded text-xs font-bold border shadow-sm',
        colorClass,
        className
      )}
      title="Confidence Score (0-100)"
    >
      {Math.round(score)}
    </span>
  )
}
