import { ChevronLeft, ChevronRight } from 'lucide-react'
import type { PaginatedMeta } from '@/types'

interface Props {
  meta: PaginatedMeta
  onPageChange: (page: number) => void
}

export function Pagination({ meta, onPageChange }: Props) {
  const { page, pages, total } = meta

  const handlePrev = () => {
    if (page > 1) onPageChange(page - 1)
  }

  const handleNext = () => {
    if (page < pages) onPageChange(page + 1)
  }

  if (total === 0) return null

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-surface-900 border-t border-slate-700/50 sm:px-6">
      <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-slate-400">
            Showing <span className="font-medium text-slate-200">{(page - 1) * meta.limit + 1}</span> to{' '}
            <span className="font-medium text-slate-200">{Math.min(page * meta.limit, total)}</span> of{' '}
            <span className="font-medium text-slate-200">{total}</span> results
          </p>
        </div>
        <div>
          <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
            <button
              onClick={handlePrev}
              disabled={page <= 1}
              className="relative inline-flex items-center rounded-l-md px-2 py-2 text-slate-400 ring-1 ring-inset ring-slate-700 hover:bg-surface-800 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="sr-only">Previous</span>
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            </button>
            <span className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-slate-200 ring-1 ring-inset ring-slate-700">
              Page {page} of {pages}
            </span>
            <button
              onClick={handleNext}
              disabled={page >= pages}
              className="relative inline-flex items-center rounded-r-md px-2 py-2 text-slate-400 ring-1 ring-inset ring-slate-700 hover:bg-surface-800 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="sr-only">Next</span>
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </nav>
        </div>
      </div>
    </div>
  )
}
