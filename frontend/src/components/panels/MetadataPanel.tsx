import { Info, Clock, CalendarDays, Key } from 'lucide-react'
import type { IndicatorDetail } from '@/types'
import { TypeBadge } from '@/components/TypeBadge'
import { StatusBadge } from '@/components/StatusBadge'
import { ConfidenceBadge } from '@/components/ConfidenceBadge'

interface Props {
  indicator: IndicatorDetail
}

export function MetadataPanel({ indicator }: Props) {
  const { latest_rationale: rationale } = indicator

  return (
    <div className="card h-[350px] flex flex-col">
      <div className="px-5 py-4 border-b border-slate-700/50 flex flex-wrap gap-4 items-start justify-between bg-surface-850/50 rounded-t-xl">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-2">
            <TypeBadge type={indicator.type} />
            <StatusBadge status={indicator.status} />
          </div>
          <h1 className="text-xl font-bold text-slate-100 font-mono tracking-tight break-words">
            {indicator.value}
          </h1>
        </div>
        <div className="text-right shrink-0">
          <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1">Current Score</p>
          <ConfidenceBadge score={indicator.current_confidence} className="text-xl px-3 py-1" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-5 scrollbar-thin">
        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <CalendarDays className="w-3.5 h-3.5" />
              <span className="text-xs font-semibold uppercase tracking-wider text-[10px]">First Seen</span>
            </div>
            <p className="text-sm font-mono text-slate-200">{new Date(indicator.first_seen).toLocaleString()}</p>
          </div>
          <div>
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <Clock className="w-3.5 h-3.5" />
              <span className="text-xs font-semibold uppercase tracking-wider text-[10px]">Last Seen</span>
            </div>
            <p className="text-sm font-mono text-slate-200">{new Date(indicator.last_seen).toLocaleString()}</p>
          </div>
          <div className="col-span-2">
            <div className="flex items-center gap-1.5 text-slate-400 mb-1">
              <Key className="w-3.5 h-3.5" />
              <span className="text-xs font-semibold uppercase tracking-wider text-[10px]">Time to Live (Expiry)</span>
            </div>
            <p className="text-sm font-mono text-slate-200">{new Date(indicator.ttl).toLocaleString()}</p>
          </div>
        </div>

        {/* Rationale Breakdown */}
        {rationale && (
          <div className="bg-surface-900 border border-slate-700/50 rounded-lg p-4">
            <div className="flex items-center gap-1.5 mb-3">
              <Info className="w-4 h-4 text-slate-400" />
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Score Breakdown</h3>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between items-center text-slate-300">
                <span>Base Evidence Sum</span>
                <span className="font-mono text-slate-200">{rationale.base_score?.toFixed(2) ?? '0.00'}</span>
              </div>
              <div className="flex justify-between items-center text-slate-300">
                <span>Enrichment Depth Bonus</span>
                <span className="font-mono text-green-400">+{rationale.enrichment_depth_bonus ?? 0}</span>
              </div>
              <div className="flex justify-between items-center text-slate-300">
                <span>Correlation Bonus</span>
                <span className="font-mono text-purple-400">+{rationale.correlation_bonus?.toFixed(2) ?? '0.00'}</span>
              </div>
              <div className="flex justify-between items-center text-slate-300">
                <span>Analyst Manual Adjustments</span>
                <span className="font-mono text-brand-400">{rationale.analyst_adjustment !== undefined ? (rationale.analyst_adjustment > 0 ? '+' : '') + rationale.analyst_adjustment.toFixed(2) : '0.00'}</span>
              </div>
              <div className="pt-2 mt-2 border-t border-slate-700/50 flex justify-between items-center font-medium">
                <span className="text-slate-300">Total Weighted Sum</span>
                <span className="font-mono text-slate-200">{rationale.weighted_sum.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center text-slate-400 mt-1">
                <span>Time Decay Factor ({rationale.days_elapsed} days)</span>
                <span className="font-mono text-red-300/80">× {rationale.decay_factor.toFixed(4)}</span>
              </div>
              <div className="pt-2 mt-2 border-t border-slate-700 flex justify-between items-center font-bold text-slate-100">
                <span>Final Confidence</span>
                <span className="font-mono text-lg text-brand-400">{rationale.score.toFixed(2)} / 100</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
