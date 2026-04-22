/**
 * IngestPage — Phase 1.3 (Manual ingestion gateway)
 *
 * Two tabs:
 *   1. Manual Entry  — paste raw indicators (auto-type-detection or explicit type:value)
 *   2. File Upload   — drag-and-drop CSV / TXT file upload (multipart POST)
 *
 * Both call POST /api/v1/indicators and display the IngestionResponse summary.
 * Both require a source to be selected first (fetched from GET /api/v1/sources).
 *
 * On success, query key ['indicators'] is invalidated so the Indicators list
 * refreshes immediately.
 */

import { useState, useCallback, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  UploadCloud, Type, FileText, CheckCircle2, AlertCircle,
  Loader2, ChevronRight, RefreshCw, List,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

import api from '@/lib/axios'
import { getSources } from '@/api/sources'
import { PageErrorBoundary } from '@/components/PageErrorBoundary'
import type { IndicatorType } from '@/types'

// ── Types ──────────────────────────────────────────────────────────────────────

interface IngestionResult {
  ingested: number
  duplicates: number
  errors: number
  error_details: Array<{ value: string; reason: string }>
  indicators: Array<{ id: string; type: string; value: string }>
}

// ── Auto type detection ────────────────────────────────────────────────────────

const IPV4_RE = /^(\d{1,3}\.){3}\d{1,3}$/
const IPV6_RE = /^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$/
const MD5_RE = /^[0-9a-fA-F]{32}$/
const SHA1_RE = /^[0-9a-fA-F]{40}$/
const SHA256_RE = /^[0-9a-fA-F]{64}$/
const URL_RE = /^https?:\/\//i

function detectType(value: string): IndicatorType {
  if (IPV4_RE.test(value)) return 'IPV4'
  if (IPV6_RE.test(value)) return 'IPV6'
  if (URL_RE.test(value)) return 'URL'
  if (SHA256_RE.test(value)) return 'SHA256'
  if (SHA1_RE.test(value)) return 'SHA1'
  if (MD5_RE.test(value)) return 'MD5'
  return 'DOMAIN'
}

/** Parse "type:value" or plain value from a single line */
function parseLine(line: string): { type: IndicatorType; value: string } | null {
  const trimmed = line.trim()
  if (!trimmed || trimmed.startsWith('#')) return null
  const colonIdx = trimmed.indexOf(':')
  const knownTypes: IndicatorType[] = ['IPV4', 'IPV6', 'DOMAIN', 'URL', 'MD5', 'SHA1', 'SHA256']
  if (colonIdx > 0) {
    const prefix = trimmed.slice(0, colonIdx).toUpperCase() as IndicatorType
    if (knownTypes.includes(prefix)) {
      return { type: prefix, value: trimmed.slice(colonIdx + 1).trim() }
    }
  }
  return { type: detectType(trimmed), value: trimmed }
}

/** Parse textarea text into preview rows */
function parseRawText(text: string): Array<{ type: IndicatorType; value: string }> {
  return text
    .split('\n')
    .map(parseLine)
    .filter((r): r is { type: IndicatorType; value: string } => r !== null)
}

// ── Result Summary Component ───────────────────────────────────────────────────

function IngestionSummary({
  result,
  onReset,
}: {
  result: IngestionResult
  onReset: () => void
}) {
  const hasErrors = result.errors > 0

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-green-400 font-mono">{result.ingested}</p>
          <p className="text-[11px] uppercase tracking-wider text-green-400/70 mt-1">Ingested</p>
        </div>
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-yellow-400 font-mono">{result.duplicates}</p>
          <p className="text-[11px] uppercase tracking-wider text-yellow-400/70 mt-1">Duplicates</p>
        </div>
        <div className={clsx(
          'rounded-lg p-4 text-center border',
          hasErrors
            ? 'bg-red-500/10 border-red-500/20'
            : 'bg-surface-900 border-slate-700/50'
        )}>
          <p className={clsx('text-2xl font-bold font-mono', hasErrors ? 'text-red-400' : 'text-slate-500')}>
            {result.errors}
          </p>
          <p className={clsx('text-[11px] uppercase tracking-wider mt-1', hasErrors ? 'text-red-400/70' : 'text-slate-600')}>
            Errors
          </p>
        </div>
      </div>

      {result.error_details.length > 0 && (
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-3 space-y-1 max-h-32 overflow-y-auto">
          <p className="text-[11px] font-bold uppercase tracking-wider text-red-400 mb-2">Validation Errors</p>
          {result.error_details.map((e, i) => (
            <p key={i} className="text-xs text-red-300 font-mono">
              <span className="text-red-400">{e.value}</span>: {e.reason}
            </p>
          ))}
        </div>
      )}

      <div className="flex gap-3 pt-2">
        <button
          onClick={onReset}
          className="btn-ghost flex items-center gap-2 flex-1 justify-center text-sm"
        >
          <RefreshCw className="w-4 h-4" /> Ingest More
        </button>
        <Link
          to="/indicators"
          className="btn-primary flex items-center gap-2 flex-1 justify-center text-sm"
        >
          <List className="w-4 h-4" /> View Indicators <ChevronRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  )
}


// ── Tab 1: Manual Entry ────────────────────────────────────────────────────────

function ManualEntryTab({
  sources,
  onResult,
}: {
  sources: Array<{ id: string; name: string }>
  onResult: (r: IngestionResult) => void
}) {
  const queryClient = useQueryClient()
  const [sourceId, setSourceId] = useState('')
  const [rawText, setRawText] = useState('')

  const parsed = parseRawText(rawText)
  const canSubmit = !!sourceId && parsed.length > 0

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = {
        source_id: sourceId,
        indicators: parsed.map((p) => ({ type: p.type, value: p.value })),
      }
      const { data } = await api.post<IngestionResult>('indicators/', payload)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['indicators'] })
      if (data.ingested > 0) {
        toast.success(`${data.ingested} indicator(s) ingested successfully`)
      } else if (data.duplicates > 0 && data.ingested === 0) {
        toast('All indicators were already known (duplicates merged)', { icon: '♻️' })
      } else {
        toast.error('No indicators were ingested — check errors below')
      }
      onResult(data)
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      toast.error(`Ingestion failed: ${msg}`)
    },
  })

  return (
    <div className="space-y-5">
      {/* Source selector */}
      <div>
        <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">
          Source <span className="text-red-400">*</span>
        </label>
        <select
          id="manual-source-select"
          className="input w-full cursor-pointer"
          value={sourceId}
          onChange={(e) => setSourceId(e.target.value)}
        >
          <option value="">— Select an intelligence source —</option>
          {sources.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        {sources.length === 0 && (
          <p className="text-xs text-yellow-400 mt-1 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            No sources registered yet. <Link to="/sources" className="underline">Add one first</Link>.
          </p>
        )}
      </div>

      {/* Raw text input */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400">
            Indicators <span className="text-red-400">*</span>
          </label>
          <span className="text-[10px] text-slate-500">
            {parsed.length > 0 ? `${parsed.length} detected` : 'one per line'}
          </span>
        </div>
        <textarea
          id="manual-indicator-input"
          className="input w-full font-mono text-sm min-h-[180px] resize-none"
          placeholder={`# One indicator per line. Type auto-detected.\n# Or prefix with type:\nIPV4:1.2.3.4\n192.168.1.100\nexample-malware.com\nURL:https://phish.site/login\nSHA256:abc123...`}
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          spellCheck={false}
        />
      </div>

      {/* Live preview */}
      {parsed.length > 0 && (
        <div className="bg-surface-950 border border-slate-700/50 rounded-lg p-3 max-h-40 overflow-y-auto">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">Preview ({parsed.length})</p>
          <div className="space-y-1">
            {parsed.slice(0, 20).map((p, i) => (
              <div key={i} className="flex items-center gap-2 text-xs font-mono">
                <span className="text-brand-400 text-[10px] bg-brand-500/10 border border-brand-500/20 px-1 rounded uppercase">
                  {p.type}
                </span>
                <span className="text-slate-300 truncate">{p.value}</span>
              </div>
            ))}
            {parsed.length > 20 && (
              <p className="text-[11px] text-slate-500">...and {parsed.length - 20} more</p>
            )}
          </div>
        </div>
      )}

      <button
        id="manual-ingest-btn"
        disabled={!canSubmit || mutation.isPending}
        onClick={() => mutation.mutate()}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        {mutation.isPending ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Processing...</>
        ) : (
          <><UploadCloud className="w-4 h-4" /> Ingest {parsed.length > 0 ? `${parsed.length} Indicator${parsed.length > 1 ? 's' : ''}` : 'Indicators'}</>
        )}
      </button>
    </div>
  )
}

// ── Tab 2: File Upload ─────────────────────────────────────────────────────────

function FileUploadTab({
  sources,
  onResult,
}: {
  sources: Array<{ id: string; name: string }>
  onResult: (r: IngestionResult) => void
}) {
  const queryClient = useQueryClient()
  const [sourceId, setSourceId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const canSubmit = !!sourceId && !!file

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) setFile(dropped)
  }, [])

  const mutation = useMutation({
    mutationFn: async () => {
      const form = new FormData()
      form.append('source_id', sourceId)
      form.append('file', file!)
      const { data } = await api.post<IngestionResult>('indicators/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['indicators'] })
      if (data.ingested > 0) {
        toast.success(`${data.ingested} indicator(s) ingested from file`)
      } else {
        toast('File processed — check results below', { icon: 'ℹ️' })
      }
      onResult(data)
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      toast.error(`File ingestion failed: ${msg}`)
    },
  })

  return (
    <div className="space-y-5">
      {/* Source selector */}
      <div>
        <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">
          Source <span className="text-red-400">*</span>
        </label>
        <select
          id="file-source-select"
          className="input w-full cursor-pointer"
          value={sourceId}
          onChange={(e) => setSourceId(e.target.value)}
        >
          <option value="">— Select an intelligence source —</option>
          {sources.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        {sources.length === 0 && (
          <p className="text-xs text-yellow-400 mt-1 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            No sources registered yet. <Link to="/sources" className="underline">Add one first</Link>.
          </p>
        )}
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={clsx(
          'border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all',
          isDragging
            ? 'border-brand-400 bg-brand-500/5'
            : file
            ? 'border-green-500/40 bg-green-500/5'
            : 'border-slate-600/50 hover:border-slate-500 hover:bg-surface-800/50'
        )}
      >
        <input
          ref={inputRef}
          id="file-upload-input"
          type="file"
          accept=".csv,.txt"
          className="hidden"
          onChange={(e) => { if (e.target.files?.[0]) setFile(e.target.files[0]) }}
        />
        {file ? (
          <div className="flex flex-col items-center gap-2">
            <CheckCircle2 className="w-10 h-10 text-green-400 mb-1" />
            <p className="text-sm font-medium text-slate-200">{file.name}</p>
            <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB · Click to change</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <UploadCloud className={clsx('w-10 h-10 mb-1', isDragging ? 'text-brand-400' : 'text-slate-500')} />
            <p className="text-sm font-medium text-slate-300">
              {isDragging ? 'Drop to upload' : 'Drop a CSV or TXT file here'}
            </p>
            <p className="text-xs text-slate-500">or click to browse · .csv or .txt</p>
          </div>
        )}
      </div>

      {/* Format hint */}
      <div className="bg-surface-950 border border-slate-700/50 rounded-lg p-3 text-xs text-slate-500 space-y-1">
        <p className="font-semibold text-slate-400">Expected formats:</p>
        <p><span className="text-brand-400 font-mono">.txt</span> — one IP/domain/URL/hash per line</p>
        <p><span className="text-brand-400 font-mono">.csv</span> — columns: <span className="font-mono">type,value</span> (header row optional)</p>
      </div>

      <button
        id="file-ingest-btn"
        disabled={!canSubmit || mutation.isPending}
        onClick={() => mutation.mutate()}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        {mutation.isPending ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Processing File...</>
        ) : (
          <><UploadCloud className="w-4 h-4" /> {file ? `Upload "${file.name}"` : 'Upload File'}</>
        )}
      </button>
    </div>
  )
}


// ── Main IngestPage Content ────────────────────────────────────────────────────

type Tab = 'manual' | 'file'

function IngestContent() {
  const [activeTab, setActiveTab] = useState<Tab>('manual')
  const [result, setResult] = useState<IngestionResult | null>(null)

  const { data: sources = [], isLoading: sourcesLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: getSources,
  })

  // Only active sources can receive ingestion
  const activeSources = sources.filter((s) => s.is_active)

  const handleResult = (r: IngestionResult) => setResult(r)
  const handleReset = () => setResult(null)

  return (
    <div className="page-container max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <UploadCloud className="w-6 h-6 text-brand-400 opacity-80" />
        <h1 className="text-xl font-bold text-slate-100 tracking-tight">Ingest Indicators</h1>
      </div>

      <div className="card p-6">
        {result ? (
          /* Result view */
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-4">
              {result.ingested > 0 ? (
                <CheckCircle2 className="w-5 h-5 text-green-400" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-400" />
              )}
              <h2 className="text-base font-semibold text-slate-200">Ingestion Complete</h2>
            </div>
            <IngestionSummary result={result} onReset={handleReset} />
          </div>
        ) : (
          <>
            {/* Tab switcher */}
            <div className="flex bg-surface-950 p-1 rounded-lg border border-slate-800 mb-6">
              <button
                id="tab-manual"
                onClick={() => setActiveTab('manual')}
                className={clsx(
                  'flex-1 flex items-center justify-center gap-2 py-2 text-sm font-semibold rounded-md transition-all',
                  activeTab === 'manual'
                    ? 'bg-brand-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                )}
              >
                <Type className="w-4 h-4" /> Manual Entry
              </button>
              <button
                id="tab-file"
                onClick={() => setActiveTab('file')}
                className={clsx(
                  'flex-1 flex items-center justify-center gap-2 py-2 text-sm font-semibold rounded-md transition-all',
                  activeTab === 'file'
                    ? 'bg-brand-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                )}
              >
                <FileText className="w-4 h-4" /> File Upload
              </button>
            </div>

            {sourcesLoading ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="w-6 h-6 animate-spin text-brand-500" />
              </div>
            ) : (
              <>
                {activeTab === 'manual' && (
                  <ManualEntryTab sources={activeSources} onResult={handleResult} />
                )}
                {activeTab === 'file' && (
                  <FileUploadTab sources={activeSources} onResult={handleResult} />
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export function IngestPage() {
  return (
    <PageErrorBoundary>
      <IngestContent />
    </PageErrorBoundary>
  )
}
