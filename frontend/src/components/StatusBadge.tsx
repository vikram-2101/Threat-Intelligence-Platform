import { clsx } from 'clsx'
import type { IndicatorStatus } from '@/types'

interface Props {
  status: IndicatorStatus
  className?: string
}

export function StatusBadge({ status, className }: Props) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider border',
        status === 'ACTIVE' && 'bg-status-active/10 text-status-active border-status-active/20',
        status === 'EXPIRED' && 'bg-status-expired/10 text-status-expired border-status-expired/20',
        status === 'REVOKED' && 'bg-status-revoked/10 text-status-revoked border-status-revoked/20',
        className
      )}
    >
      {status}
    </span>
  )
}
