import { clsx } from 'clsx'
import type { IndicatorType } from '@/types'
import { Hash, Globe, MapPin, Link2 } from 'lucide-react'

interface Props {
  type: IndicatorType
  className?: string
}

export function TypeBadge({ type, className }: Props) {
  let Icon = Link2
  let colorClass = 'bg-slate-700/50 text-slate-300 border-slate-600'

  switch (type) {
    case 'IPV4':
    case 'IPV6':
      Icon = MapPin
      colorClass = 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      break
    case 'DOMAIN':
      Icon = Globe
      colorClass = 'bg-purple-500/10 text-purple-400 border-purple-500/20'
      break
    case 'URL':
      Icon = Link2
      colorClass = 'bg-pink-500/10 text-pink-400 border-pink-500/20'
      break
    case 'MD5':
    case 'SHA1':
    case 'SHA256':
      Icon = Hash
      colorClass = 'bg-slate-500/10 text-slate-400 border-slate-500/20'
      break
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium border shadow-sm',
        colorClass,
        className
      )}
    >
      <Icon className="w-3 h-3 opacity-70" />
      {type}
    </span>
  )
}
