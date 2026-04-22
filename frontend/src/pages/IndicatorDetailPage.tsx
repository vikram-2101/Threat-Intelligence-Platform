import { useParams, Link } from 'react-router-dom'
import { useQueries } from '@tanstack/react-query'
import { ArrowLeft, AlertCircle, Loader2 } from 'lucide-react'

import { getIndicator, getIndicatorCorrelations } from '@/api/indicators'
import { PageErrorBoundary } from '@/components/PageErrorBoundary'
import { MetadataPanel } from '@/components/panels/MetadataPanel'
import { TimelinePanel } from '@/components/panels/TimelinePanel'
import { EvidencePanel } from '@/components/panels/EvidencePanel'
import { CorrelationPanel } from '@/components/panels/CorrelationPanel'
import { ActionsPanel } from '@/components/panels/ActionsPanel'

function IndicatorDetailContent() {
  const { id } = useParams<{ id: string }>()

  // Parallel data fetching using TanStack Query
  const [indicatorQuery, correlationQuery] = useQueries({
    queries: [
      {
        queryKey: ['indicator', id],
        queryFn: () => getIndicator(id!),
        enabled: !!id,
      },
      {
        queryKey: ['correlation', id],
        queryFn: () => getIndicatorCorrelations(id!),
        enabled: !!id,
      },
    ],
  })

  // Loading State
  if (indicatorQuery.isLoading || correlationQuery.isLoading) {
    return (
      <div className="page-container flex flex-col items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin mb-4" />
        <h2 className="text-sm font-semibold text-slate-300">Loading Indicator Context...</h2>
      </div>
    )
  }

  // Error State
  if (indicatorQuery.isError || !indicatorQuery.data) {
    return (
      <div className="page-container">
        <Link to="/indicators" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to indicators
        </Link>
        <div className="card p-8 flex flex-col items-center text-center">
          <div className="p-3 bg-red-500/10 rounded-full border border-red-500/20 mb-4">
            <AlertCircle className="w-6 h-6 text-red-400" />
          </div>
          <h2 className="text-lg font-semibold text-slate-200 mb-2">Indicator Not Found</h2>
          <p className="text-sm text-slate-400 max-w-sm">
            The requested indicator could not be loaded or you do not have permission to view it.
          </p>
        </div>
      </div>
    )
  }

  const indicator = indicatorQuery.data
  const correlations = correlationQuery.data

  return (
    <div className="page-container pb-12">
      <div className="mb-6">
        <Link to="/indicators" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to indicators
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Panel 1: Metadata & Score Rationale */}
        <MetadataPanel indicator={indicator} />

        {/* Panel 3: Confidence Timeline visualization */}
        <TimelinePanel history={indicator.confidence_history} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Panel 2: Evidence Accordion (Takes 8 columns) */}
        <div className="lg:col-span-8">
          <EvidencePanel evidenceList={indicator.evidence} />
        </div>

        {/* Right Stack: Actions + Correlations (Takes 4 columns) */}
        <div className="lg:col-span-4 space-y-6 h-full flex flex-col">
          <ActionsPanel indicator={indicator} />
          <div className="flex-1 min-h-[300px]">
            <CorrelationPanel data={correlations} />
          </div>
        </div>
      </div>
    </div>
  )
}

export function IndicatorDetailPage() {
  return (
    <PageErrorBoundary>
      <IndicatorDetailContent />
    </PageErrorBoundary>
  )
}
