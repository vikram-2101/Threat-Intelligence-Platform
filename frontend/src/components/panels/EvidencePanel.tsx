import { useState } from 'react'
import { ChevronDown, ChevronRight, FileText, CheckCircle2, XCircle, RotateCcw } from 'lucide-react'
import { clsx } from 'clsx'
import type { Evidence } from '@/types'

interface Props {
  evidenceList: Evidence[]
}

export function EvidencePanel({ evidenceList }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const toggle = (id: string) => {
    setExpandedId(prev => (prev === id ? null : id))
  }

  // Sort by newest first
  const sorted = [...evidenceList].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

  return (
    <div className="card h-full flex flex-col">
      <div className="px-5 py-4 border-b border-slate-700/50 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-brand-400" />
          <h2 className="text-sm font-semibold text-slate-200">Evidence & Enrichments</h2>
        </div>
        <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
          {sorted.length} Records
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-2 scrollbar-thin">
        {sorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-slate-500">
            <p className="text-sm">No evidence records found.</p>
          </div>
        ) : (
          <div className="space-y-2 relative">
            {/* Simple timeline line behind items */}
            <div className="absolute top-4 bottom-4 left-5 w-px bg-slate-700/50 z-0 hidden sm:block"></div>

            {sorted.map((ev) => {
              const isExpanded = expandedId === ev.id
              return (
                <div 
                  key={ev.id} 
                  className={clsx(
                    "relative z-10 bg-surface-850 border rounded-lg transition-colors overflow-hidden",
                    ev.reversed ? "border-slate-800 opacity-60" : "border-slate-700/50"
                  )}
                >
                  <button
                    onClick={() => toggle(ev.id)}
                    className="w-full text-left px-4 py-3 flex items-center gap-4 hover:bg-surface-800 transition-colors focus:outline-none focus:bg-surface-800"
                  >
                    <div className="hidden sm:flex shrink-0 w-2.5 h-2.5 rounded-full bg-surface-850 border-2 border-brand-500 ml-0.5" />
                    
                    <div className="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-[11px] uppercase tracking-wider font-bold text-slate-300">
                            {ev.evidence_type.replace(/_/g, ' ')}
                          </span>
                          {ev.reversed && (
                            <span className="inline-flex items-center gap-1 text-[9px] uppercase font-bold text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700 shrink-0">
                              <RotateCcw className="w-2.5 h-2.5" /> Reversed
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 font-mono">
                          {new Date(ev.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex items-center justify-end gap-3 shrink-0">
                        <span className={clsx(
                          "text-xs font-mono font-bold px-2 py-1 rounded bg-surface-900 border",
                          ev.reversed 
                            ? "text-slate-500 border-slate-700"
                            : ev.confidence_delta > 0 
                              ? "text-brand-400 border-brand-500/20" 
                              : ev.confidence_delta < 0
                                ? "text-red-400 border-red-500/20"
                                : "text-slate-400 border-slate-700"
                        )}>
                          {ev.confidence_delta > 0 && !ev.reversed ? '+' : ''}{ev.confidence_delta}
                        </span>
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-slate-500" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-slate-500" />
                        )}
                      </div>
                    </div>
                  </button>
                  
                  {isExpanded && (
                    <div className="px-4 pb-4 sm:pl-10 text-sm border-t border-slate-700/50 bg-surface-900/50 pt-3">
                      <div className="mb-3 grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-0.5">Record ID</p>
                          <p className="text-xs font-mono text-slate-400">{ev.id}</p>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-0.5">Status</p>
                          <p className="text-xs text-slate-300 flex items-center gap-1">
                            {ev.reversed ? (
                              <><XCircle className="w-3.5 h-3.5 text-red-400" /> Reversed on {ev.reversed_at ? new Date(ev.reversed_at).toLocaleDateString() : 'Unknown'}</>
                            ) : (
                              <><CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> Active</>
                            )}
                          </p>
                        </div>
                      </div>
                      
                      <div>
                        <p className="text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-1.5">Raw Payload</p>
                        <div className="bg-surface-950 p-3 rounded border border-slate-800 overflow-x-auto">
                          <pre className="text-[11px] font-mono text-slate-300 leading-tight">
                            {JSON.stringify(ev.raw_payload, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
