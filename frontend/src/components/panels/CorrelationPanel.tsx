import { Link2, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { CorrelationResponse } from '@/types'

interface Props {
  data?: CorrelationResponse
}

export function CorrelationPanel({ data }: Props) {
  const correlations = data?.correlations || []

  return (
    <div className="card h-full flex flex-col">
      <div className="px-5 py-4 border-b border-slate-700/50 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2">
          <Link2 className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-semibold text-slate-200">Indicator Correlations</h2>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
          {data?.total ?? 0} Links
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
        {correlations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-slate-500">
            <p className="text-sm">No correlations found.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {correlations.map((corr) => {
              // Extract target indicator if available from raw_payload (based on backend engine structure)
              const payload = corr.raw_payload as any
              const targetValues = payload.correlated_ips || payload.related_domains || payload.sources || []
              const label = typeof targetValues[0] === 'string' ? targetValues.join(', ') : 'Infrastructure link'

              return (
                <div key={corr.evidence_id} className="bg-surface-850 border border-slate-700/50 p-3 rounded-lg hover:border-slate-600 transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 bg-purple-500/10 border border-purple-500/20 rounded text-[10px] uppercase font-bold text-purple-300">
                        {corr.correlation_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <span className="text-xs font-mono font-bold text-brand-400 bg-surface-900 border border-brand-500/20 px-1.5 py-0.5 rounded">
                      +{corr.confidence_delta}
                    </span>
                  </div>
                  
                  <p className="text-sm text-slate-300 font-mono mb-2 truncate">
                    {label}
                  </p>
                  
                  <div className="flex items-center justify-between border-t border-slate-700/50 pt-2 mt-2">
                    <span className="text-xs text-slate-500 font-mono">
                      {new Date(corr.timestamp).toLocaleDateString()}
                    </span>
                    <Link to={`/indicators`} className="inline-flex items-center gap-1 text-[11px] text-brand-400 hover:text-brand-300 font-medium">
                      Investigate <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
