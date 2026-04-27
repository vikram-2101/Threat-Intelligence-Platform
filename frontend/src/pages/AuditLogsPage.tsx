import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchAuditLogs } from '@/api/audit_logs'
import { Pagination } from '@/components/Pagination'
import { format } from 'date-fns'
import { Activity, Search, ServerCrash } from 'lucide-react'

export function AuditLogsPage() {
  const [page, setPage] = useState(1)
  const [action, setAction] = useState('')
  const [entityType, setEntityType] = useState('')

  const { data, isLoading, isError } = useQuery({
    queryKey: ['audit-logs', page, action, entityType],
    queryFn: () => fetchAuditLogs({ page, limit: 50, action: action || undefined, entity_type: entityType || undefined }),
  })

  return (
    <div className="flex flex-col h-full bg-surface-900">
      {/* Header */}
      <header className="flex flex-col gap-4 p-6 shrink-0 border-b border-surface-800 bg-surface-950">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Activity className="w-6 h-6 text-brand-400" />
            Audit Logs
          </h1>
          <p className="text-sm text-slate-400 mt-1">Immutable track of all system actions, enrichments, and operations.</p>
        </div>
        
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Filter by action (e.g. EXPORT_INDICATORS, ANALYST_ACTION, REVERSE)..."
              value={action}
              onChange={(e) => {
                setAction(e.target.value)
                setPage(1)
              }}
              className="w-full pl-9 pr-3 py-2 bg-surface-800 border border-slate-700/50 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>
          <div className="relative flex items-center">
            <input
              type="text"
              placeholder="Filter by entity type (e.g. indicators, evidence)..."
              value={entityType}
              onChange={(e) => {
                setEntityType(e.target.value)
                setPage(1)
              }}
              className="w-full px-3 py-2 bg-surface-800 border border-slate-700/50 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>
        </div>
      </header>

      {/* Main Table */}
      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex gap-2 items-center text-slate-400 animate-pulse">
              <Activity className="w-5 h-5" />
              <span>Querying massive data bounds...</span>
            </div>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-2">
             <ServerCrash className="w-10 h-10 text-red-400" />
             <span>Failed to load Audit Logs. Make sure you have Admin permissions mapping your User!</span>
          </div>
        ) : (
          <div className="bg-surface-950 border border-surface-800 rounded-xl shadow-sm overflow-hidden flex flex-col min-h-[500px]">
             <div className="overflow-x-auto flex-1">
                <table className="w-full text-left border-collapse text-sm whitespace-nowrap">
                  <thead className="bg-surface-800/50 text-slate-400 font-medium border-b border-surface-800 sticky top-0 z-10">
                    <tr>
                      <th className="px-4 py-3">Timestamp</th>
                      <th className="px-4 py-3">Action</th>
                      <th className="px-4 py-3">Entity Type</th>
                      <th className="px-4 py-3">Entity ID</th>
                      <th className="px-4 py-3 min-w-[300px]">Payload Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-800">
                    {data?.data.map((log) => (
                      <tr key={log.id} className="hover:bg-surface-800/30 transition-colors group">
                        <td className="px-4 py-3 text-slate-400">
                          {format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                        </td>
                        <td className="px-4 py-3 font-semibold text-brand-300 tracking-wider text-xs">
                          {log.action}
                        </td>
                        <td className="px-4 py-3 text-slate-300">
                          {log.entity_type || '-'}
                        </td>
                        <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                          {log.entity_id || '-'}
                        </td>
                        <td className="px-4 py-3">
                          <code className="text-xs text-slate-400 bg-surface-900 px-2 py-1 rounded inline-block max-w-[400px] overflow-hidden text-ellipsis whitespace-nowrap border border-slate-700/50">
                            {JSON.stringify(log.details)}
                          </code>
                        </td>
                      </tr>
                    ))}
                    {data?.data.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                          No audit logs found matching criteria.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
             </div>
             
             {/* Footer Pagination */}
             {data?.meta && data.meta.pages > 1 && (
                <div className="bg-surface-950 px-4 py-3 border-t border-surface-800 sticky bottom-0">
                  <Pagination
                    currentPage={data.meta.page}
                    totalPages={data.meta.pages}
                    onPageChange={setPage}
                  />
                </div>
              )}
          </div>
        )}
      </div>
    </div>
  )
}
