import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { List, Search, AlertCircle, Loader2, FilterX, Trash2 } from 'lucide-react'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'

import { getIndicators, clearIndicators } from '@/api/indicators'
import { PageErrorBoundary } from '@/components/PageErrorBoundary'
import { TypeBadge } from '@/components/TypeBadge'
import { StatusBadge } from '@/components/StatusBadge'
import { ConfidenceBadge } from '@/components/ConfidenceBadge'
import { Pagination } from '@/components/Pagination'
import { RangeSlider } from '@/components/RangeSlider'
import { useDebounce } from '@/hooks/useDebounce'

import type { IndicatorFilters, IndicatorType, IndicatorStatus } from '@/types'

const indicatorTypes: IndicatorType[] = ['IPV4', 'IPV6', 'DOMAIN', 'URL', 'MD5', 'SHA1', 'SHA256']
const indicatorStatuses: IndicatorStatus[] = ['ACTIVE', 'EXPIRED', 'REVOKED']

function IndicatorsContent() {
  const [filters, setFilters] = useState<IndicatorFilters>({
    page: 1,
    limit: 15,
  })

  // Local state for debounced inputs
  const [searchValue, setSearchValue] = useState('')
  const [searchSource, setSearchSource] = useState('')
  const [confidenceRange, setConfidenceRange] = useState<[number, number]>([0, 100])

  const debouncedSearchValue = useDebounce(searchValue, 300)
  const debouncedSearchSource = useDebounce(searchSource, 300)
  const debouncedConfidence = useDebounce(confidenceRange, 300)

  // Sync debounced values to actual query filters
  useEffect(() => {
    setFilters((prev) => ({
      ...prev,
      page: 1, // reset page on new search
      value: debouncedSearchValue || undefined,
      source: debouncedSearchSource || undefined,
      confidence_min: debouncedConfidence[0],
      confidence_max: debouncedConfidence[1],
    }))
  }, [debouncedSearchValue, debouncedSearchSource, debouncedConfidence])

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['indicators', filters],
    queryFn: () => getIndicators(filters),
    placeholderData: (prev) => prev, // keeps previous data while fetching new to prevent flicker
  })

  const queryClient = useQueryClient()

  const clearMutation = useMutation({
    mutationFn: () => clearIndicators(),
    onSuccess: () => {
      toast.success('All indicators cleared successfully')
      queryClient.invalidateQueries({ queryKey: ['indicators'] })
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      toast.error(`Failed to clear indicators: ${msg}`)
    },
  })

  const resetFilters = () => {
    setSearchValue('')
    setSearchSource('')
    setConfidenceRange([0, 100])
    setFilters({ page: 1, limit: 15 })
  }

  return (
    <div className="page-container flex flex-col h-full gap-4">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <List className="w-6 h-6 text-brand-400 opacity-80" />
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Indicators</h1>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={resetFilters} className="btn-ghost text-xs">
            <FilterX className="w-4 h-4" /> Reset Filters
          </button>
          <button
            onClick={() => {
              if (window.confirm('Are you sure you want to completely delete all indicators? This action cannot be undone.')) {
                clearMutation.mutate()
              }
            }}
            disabled={clearMutation.isPending}
            className="btn-danger flex items-center gap-2 text-xs py-1 px-3 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 rounded"
          >
            <Trash2 className="w-3.5 h-3.5" />
            {clearMutation.isPending ? 'Clearing...' : 'Clear All'}
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card p-4 shrink-0 shadow-md flex flex-col lg:flex-row gap-4 items-end">

        <div className="flex-1 w-full relative">
          <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">Value</label>
          <Search className="absolute left-3 top-[28px] w-4 h-4 text-slate-500" />
          <input
            type="text"
            className="input pl-9"
            placeholder="Search indicator value..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
        </div>
        
        <div className="w-full lg:w-48 shrink-0 relative">
          <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">Source</label>
          <input
            type="text"
            className="input"
            placeholder="Filter by source..."
            value={searchSource}
            onChange={(e) => setSearchSource(e.target.value)}
          />
        </div>

        <div className="w-full lg:w-40 shrink-0">
          <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">Type</label>
          <select
            className="input cursor-pointer"
            value={filters.type || ''}
            onChange={(e) => setFilters((f) => ({ ...f, type: (e.target.value as IndicatorType) || undefined, page: 1 }))}
          >
            <option value="">Any</option>
            {indicatorTypes.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div className="w-full lg:w-40 shrink-0">
          <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">Status</label>
          <select
            className="input cursor-pointer"
            value={filters.status || ''}
            onChange={(e) => setFilters((f) => ({ ...f, status: (e.target.value as IndicatorStatus) || undefined, page: 1 }))}
          >
            <option value="">Any</option>
            {indicatorStatuses.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="w-full lg:w-64 shrink-0 px-2 pb-1">
          <div className="flex justify-between items-center mb-2">
            <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400">Confidence</label>
            <span className="text-xs text-slate-500 font-mono">
              {confidenceRange[0]} - {confidenceRange[1]}
            </span>
          </div>
          <RangeSlider
            min={0}
            max={100}
            value={confidenceRange}
            onValueChange={setConfidenceRange}
          />
        </div>
      </div>

      {/* Main Table Area */}
      <div className="card flex-1 flex flex-col min-h-0 relative overflow-hidden shadow-xl">
        {isError && (
          <div className="absolute inset-x-4 top-4 z-10 flex items-start gap-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p className="text-sm text-red-300">
              Failed to load indicators: {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        )}

        {/* Loading overlay for refetches */}
        {isLoading && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-surface-900/50 backdrop-blur-sm">
            <div className="flex items-center gap-3 bg-surface-800 px-4 py-2 rounded-lg shadow-xl border border-slate-700">
              <Loader2 className="w-5 h-5 animate-spin text-brand-500" />
              <span className="text-sm font-medium text-slate-300">Loading indicators...</span>
            </div>
          </div>
        )}

        <div className="flex-1 overflow-auto">
          <table className="w-full text-left border-collapse isolate">
            <thead className="sticky top-0 z-10 bg-surface-850/95 backdrop-blur shadow-[0_1px_0_0_rgba(255,255,255,0.05)]">
              <tr className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                <th className="px-4 py-3 font-medium">Value</th>
                <th className="px-4 py-3 font-medium whitespace-nowrap">Type</th>
                <th className="px-4 py-3 font-medium text-center">Score</th>
                <th className="px-4 py-3 font-medium text-center">Status</th>
                <th className="px-4 py-3 font-medium hidden md:table-cell">Sources</th>
                <th className="px-4 py-3 font-medium hidden lg:table-cell">Last Seen</th>
                <th className="px-4 py-3 font-medium text-right">TTL</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {data?.data.map((ind) => (
                <tr
                  key={ind.id}
                  className={clsx(
                    'table-row-base group',
                    (ind.status === 'EXPIRED' || ind.status === 'REVOKED') && 'opacity-60 grayscale-[0.5] hover:grayscale-0 transition-all'
                  )}
                >
                  <td className="px-4 py-3">
                    <Link to={`/indicators/${ind.id}`} className="block">
                      <span className="mono-value font-medium text-slate-200 group-hover:text-brand-400 transition-colors">
                        {ind.value}
                      </span>
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <Link to={`/indicators/${ind.id}`} className="block">
                      <TypeBadge type={ind.type} />
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <Link to={`/indicators/${ind.id}`} className="block">
                      <ConfidenceBadge score={ind.current_confidence} />
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <Link to={`/indicators/${ind.id}`} className="block">
                      <StatusBadge status={ind.status} />
                    </Link>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <Link to={`/indicators/${ind.id}`} className="block">
                      <div className="flex flex-wrap gap-1">
                        {ind.source_names.slice(0, 2).map((src, i) => (
                          <span key={i} className="text-[10px] text-slate-400 bg-surface-900 border border-slate-700 px-1 rounded truncate max-w-[80px]">
                            {src}
                          </span>
                        ))}
                        {ind.source_names.length > 2 && (
                          <span className="text-[10px] text-slate-500 font-medium">+{ind.source_names.length - 2}</span>
                        )}
                        {ind.source_names.length === 0 && (
                          <span className="text-[10px] text-slate-500 italic">System</span>
                        )}
                      </div>
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs hidden lg:table-cell whitespace-nowrap">
                    <Link to={`/indicators/${ind.id}`} className="block">
                      {new Date(ind.last_seen).toLocaleDateString()} {new Date(ind.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <Link to={`/indicators/${ind.id}`} className="block">
                      <span className="text-[11px] font-mono text-slate-500">
                        {new Date(ind.ttl).toLocaleDateString()}
                      </span>
                    </Link>
                  </td>
                </tr>
              ))}
              
              {data?.data.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center gap-2">
                      <Search className="w-8 h-8 text-slate-600 mb-2" />
                      <p className="text-sm font-medium">No indicators found</p>
                      <p className="text-xs text-slate-500">Try adjusting your filters or search constraints.</p>
                      <button onClick={resetFilters} className="btn-ghost mt-2">Clear Filters</button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {data?.meta && data.meta.total > 0 && (
          <Pagination
            meta={data.meta}
            onPageChange={(page) => setFilters((f) => ({ ...f, page }))}
          />
        )}
      </div>
    </div>
  )
}

export function IndicatorsPage() {
  return (
    <PageErrorBoundary>
      <IndicatorsContent />
    </PageErrorBoundary>
  )
}
