/**
 * PageErrorBoundary — catches runtime errors in page-level components.
 * Agent.md §12: "Error boundaries on all page-level components."
 *
 * Must be a class component — React error boundaries cannot be functional hooks.
 */

import { Component, type ReactNode, type ErrorInfo } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class PageErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[TIP] Uncaught error in page:', error, info)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4 text-center p-8">
          <div className="p-4 rounded-full bg-red-500/10 border border-red-500/20">
            <AlertTriangle className="w-8 h-8 text-red-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-100 mb-1">Something went wrong</h2>
            <p className="text-sm text-slate-400 max-w-md">
              {this.state.error?.message ?? 'An unexpected error occurred on this page.'}
            </p>
          </div>
          <button
            onClick={this.handleReset}
            className="btn-secondary text-sm"
          >
            Try again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
