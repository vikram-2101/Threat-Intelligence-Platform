/**
 * SourcesPage — Phase 1.1 (Source CRUD)
 *
 * Full sources management:
 *   - List all registered sources in a table
 *   - ADMIN: create / edit / delete sources via modal form
 *   - Trust tier auto-fills the default_weight per Agent.md §5
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Database, Plus, Pencil, Trash2, CheckCircle2, XCircle, ShieldCheck, Loader2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

import { getSources, createSource, updateSource, deleteSource, pullSource } from '@/api/sources'
import { ConfirmationModal } from '@/components/ConfirmationModal'
import { PageErrorBoundary } from '@/components/PageErrorBoundary'
import type { Source, SourceCreate, SourceUpdate, SourceCategory, TrustTier } from '@/types'

// ── Constants (Agent.md §5 — Trust weight map, hardcoded) ─────────────────────

const TRUST_WEIGHT_MAP: Record<TrustTier, number> = {
  LOW: 0.3,
  MEDIUM: 0.6,
  HIGH: 1.0,
}

const TRUST_TIER_COLORS: Record<TrustTier, string> = {
  LOW: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  MEDIUM: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  HIGH: 'text-green-400 bg-green-500/10 border-green-500/20',
}

const CATEGORY_COLORS: Record<SourceCategory, string> = {
  community: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
  research: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  commercial: 'text-brand-400 bg-brand-500/10 border-brand-500/20',
  internal: 'text-slate-300 bg-slate-500/10 border-slate-500/20',
}

// ── Empty form state ───────────────────────────────────────────────────────────

const emptyForm = (): SourceCreate => ({
  name: '',
  category: 'community',
  trust_tier: 'LOW',
  default_weight: TRUST_WEIGHT_MAP['LOW'],
  intent_description: '',
  pull_url: '',
  pull_schedule: '',
  is_active: true,
})

// ── Source Form Modal ──────────────────────────────────────────────────────────

interface SourceFormModalProps {
  isOpen: boolean
  editTarget: Source | null
  onClose: () => void
}

function SourceFormModal({ isOpen, editTarget, onClose }: SourceFormModalProps) {
  const queryClient = useQueryClient()
  const isEdit = !!editTarget

  const [form, setForm] = useState<SourceCreate>(() =>
    editTarget
      ? {
        name: editTarget.name,
        category: editTarget.category,
        trust_tier: editTarget.trust_tier,
        default_weight: editTarget.default_weight,
        intent_description: editTarget.intent_description ?? '',
        pull_url: editTarget.pull_url ?? '',
        pull_schedule: editTarget.pull_schedule ?? '',
        is_active: editTarget.is_active,
      }
      : emptyForm()
  )

  // Sync form when editTarget changes
  const resetForm = (target: Source | null) => {
    setForm(
      target
        ? {
          name: target.name,
          category: target.category,
          trust_tier: target.trust_tier,
          default_weight: target.default_weight,
          intent_description: target.intent_description ?? '',
          pull_url: target.pull_url ?? '',
          pull_schedule: target.pull_schedule ?? '',
          is_active: target.is_active,
        }
        : emptyForm()
    )
  }

  const handleTierChange = (tier: TrustTier) => {
    setForm((f) => ({ ...f, trust_tier: tier, default_weight: TRUST_WEIGHT_MAP[tier] }))
  }

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['sources'] })

  const createMutation = useMutation({
    mutationFn: (payload: SourceCreate) => createSource(payload),
    onSuccess: () => {
      toast.success('Source created successfully')
      invalidate()
      onClose()
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      toast.error(`Failed to create source: ${msg}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: (payload: SourceUpdate) => updateSource(editTarget!.id, payload),
    onSuccess: () => {
      toast.success('Source updated successfully')
      invalidate()
      onClose()
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      toast.error(`Failed to update source: ${msg}`)
    },
  })

  const isPending = createMutation.isPending || updateMutation.isPending

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) {
      toast.error('Source name is required')
      return
    }
    const payload: SourceCreate = {
      ...form,
      intent_description: form.intent_description?.trim() || undefined,
      pull_url: form.pull_url?.trim() || undefined,
      pull_schedule: form.pull_schedule?.trim() || undefined,
    }
    if (isEdit) {
      updateMutation.mutate(payload)
    } else {
      createMutation.mutate(payload)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-surface-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-brand-400" />
            <h2 className="text-sm font-semibold text-slate-100">
              {isEdit ? 'Edit Source' : 'Register New Source'}
            </h2>
          </div>
          <button
            onClick={() => { onClose(); resetForm(null) }}
            className="text-slate-500 hover:text-slate-300 transition-colors text-lg leading-none"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">

          {/* Name */}
          <div>
            <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">
              Source Name <span className="text-red-400">*</span>
            </label>
            <input
              id="source-name"
              type="text"
              className="input w-full"
              placeholder="e.g. AlienVault OTX"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              required
            />
          </div>

          {/* Category + Trust Tier (2-col) */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">
                Category <span className="text-red-400">*</span>
              </label>
              <select
                id="source-category"
                className="input w-full cursor-pointer"
                value={form.category}
                onChange={(e) => setForm((f) => ({ ...f, category: e.target.value as SourceCategory }))}
              >
                <option value="community">Community</option>
                <option value="research">Research</option>
                <option value="commercial">Commercial</option>
                <option value="internal">Internal</option>
              </select>
            </div>
            <div>
              <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">
                Trust Tier <span className="text-red-400">*</span>
              </label>
              <select
                id="source-trust-tier"
                className="input w-full cursor-pointer"
                value={form.trust_tier}
                onChange={(e) => handleTierChange(e.target.value as TrustTier)}
              >
                <option value="LOW">LOW (weight 0.3)</option>
                <option value="MEDIUM">MEDIUM (weight 0.6)</option>
                <option value="HIGH">HIGH (weight 1.0)</option>
              </select>
            </div>
          </div>

          {/* Default Weight (read-only, auto from tier) */}
          <div>
            <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">
              Default Weight (auto-set from Trust Tier)
            </label>
            <div className="input w-full text-slate-300 bg-surface-950/50 cursor-not-allowed select-none font-mono text-sm">
              {form.default_weight.toFixed(1)}
            </div>
          </div>

          {/* Intent Description */}
          <div>
            <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">
              Intent Description
            </label>
            <textarea
              id="source-intent"
              className="input w-full min-h-[64px] resize-none text-sm"
              placeholder="What kind of indicators does this feed produce?"
              value={form.intent_description}
              onChange={(e) => setForm((f) => ({ ...f, intent_description: e.target.value }))}
            />
          </div>

          {/* Pull URL */}
          <div>
            <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">
              Pull URL <span className="text-slate-600 font-normal">(optional — for scheduled feeds)</span>
            </label>
            <input
              id="source-pull-url"
              type="text"
              className="input w-full text-sm"
              placeholder="https://feeds.example.com/indicators.txt"
              value={form.pull_url}
              onChange={(e) => setForm((f) => ({ ...f, pull_url: e.target.value }))}
            />
          </div>

          {/* Is Active toggle */}
          <div className="flex items-center justify-between py-2 border-t border-slate-700/50">
            <div>
              <p className="text-sm font-medium text-slate-300">Active</p>
              <p className="text-[11px] text-slate-500">Inactive sources cannot receive ingested indicators</p>
            </div>
            <button
              id="source-active-toggle"
              type="button"
              onClick={() => setForm((f) => ({ ...f, is_active: !f.is_active }))}
              className={clsx(
                'relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors',
                form.is_active ? 'bg-brand-500' : 'bg-slate-600'
              )}
            >
              <span
                className={clsx(
                  'pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform transition-transform',
                  form.is_active ? 'translate-x-5' : 'translate-x-0'
                )}
              />
            </button>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={() => { onClose(); resetForm(null) }}
              className="btn-ghost flex-1 text-sm"
            >
              Cancel
            </button>
            <button
              id="source-submit-btn"
              type="submit"
              disabled={isPending || !form.name.trim()}
              className="btn-primary flex-1 text-sm"
            >
              {isPending ? 'Saving...' : isEdit ? 'Save Changes' : 'Register Source'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Main Sources Content ───────────────────────────────────────────────────────

function SourcesContent() {
  const queryClient = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<Source | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Source | null>(null)

  const { data: sources, isLoading, isError } = useQuery({
    queryKey: ['sources'],
    queryFn: getSources,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteSource(id),
    onSuccess: () => {
      toast.success('Source removed')
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      setDeleteTarget(null)
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      toast.error(`Failed to delete source: ${msg}`)
    },
  })

  const openCreate = () => {
    setEditTarget(null)
    setModalOpen(true)
  }

  const openEdit = (source: Source) => {
    setEditTarget(source)
    setModalOpen(true)
  }

  return (
    <div className="page-container flex flex-col h-full gap-4">
      {/* Page Header */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Database className="w-6 h-6 text-brand-400 opacity-80" />
          <h1 className="text-xl font-bold text-slate-100 tracking-tight">Sources</h1>
          {sources && (
            <span className="text-xs text-slate-500 bg-surface-800 border border-slate-700 px-2 py-0.5 rounded-full font-mono">
              {sources.length} registered
            </span>
          )}
        </div>
        <button
          id="add-source-btn"
          onClick={openCreate}
          className="btn-primary flex items-center gap-2 text-sm"
        >
          <Plus className="w-4 h-4" />
          Add Source
        </button>
      </div>

      {/* Table */}
      <div className="card flex-1 flex flex-col min-h-0 relative overflow-hidden shadow-xl">
        {isLoading && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-surface-900/50 backdrop-blur-sm">
            <div className="flex items-center gap-3 bg-surface-800 px-4 py-2 rounded-lg shadow-xl border border-slate-700">
              <Loader2 className="w-5 h-5 animate-spin text-brand-500" />
              <span className="text-sm font-medium text-slate-300">Loading sources...</span>
            </div>
          </div>
        )}

        {isError && (
          <div className="p-6 text-center text-red-400 text-sm">
            Failed to load sources. Check that the backend is running.
          </div>
        )}

        <div className="flex-1 overflow-auto">
          <table className="w-full text-left border-collapse">
            <thead className="sticky top-0 z-10 bg-surface-850/95 backdrop-blur shadow-[0_1px_0_0_rgba(255,255,255,0.05)]">
              <tr className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium">Trust Tier</th>
                <th className="px-4 py-3 font-medium text-center">Weight</th>
                <th className="px-4 py-3 font-medium text-center">Status</th>
                <th className="px-4 py-3 font-medium">Feed Info</th>
                <th className="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {sources?.map((src) => (
                <tr key={src.id} className="table-row-base group">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-3.5 h-3.5 text-brand-500/60 shrink-0" />
                      <span className="text-sm font-medium text-slate-200">{src.name}</span>
                    </div>
                    {src.intent_description && (
                      <p className="text-[11px] text-slate-500 mt-0.5 ml-5 truncate max-w-xs">
                        {src.intent_description}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={clsx(
                      'text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border',
                      CATEGORY_COLORS[src.category]
                    )}>
                      {src.category}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={clsx(
                      'text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border',
                      TRUST_TIER_COLORS[src.trust_tier]
                    )}>
                      {src.trust_tier}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-xs font-mono text-slate-300">{src.default_weight.toFixed(1)}</span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {src.is_active ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-green-400 bg-green-500/10 border border-green-500/20 px-1.5 py-0.5 rounded">
                        <CheckCircle2 className="w-3 h-3" /> Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-slate-500 bg-slate-500/10 border border-slate-500/20 px-1.5 py-0.5 rounded">
                        <XCircle className="w-3 h-3" /> Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs whitespace-nowrap">
                    {src.pull_url ? (
                      <div className="flex flex-col gap-0.5 text-[11px]">
                        <span className="text-slate-300 font-mono max-w-[120px] truncate" title={src.pull_url}>
                          {src.pull_url}
                        </span>
                        {src.pull_schedule && (
                          <span className="text-slate-500 font-mono">📅 {src.pull_schedule}</span>
                        )}
                        {src.last_pull_status && (
                          <span className={clsx(
                            "text-[10px] font-semibold mt-0.5",
                            src.last_pull_status.includes("success") ? "text-green-400" : "text-amber-400"
                          )}>
                            Last Status: {src.last_pull_status}
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-600 italic">None</span>
                    )}
                  </td>

                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {src.pull_url && (
                        <PullButton sourceId={src.id} />
                      )}
                      <button
                        title="Edit source"
                        onClick={() => openEdit(src)}
                        className="p-1.5 rounded text-slate-500 hover:text-brand-400 hover:bg-brand-500/10 transition-colors"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button
                        title="Delete source"
                        onClick={() => setDeleteTarget(src)}
                        className="p-1.5 rounded text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>

                </tr>
              ))}

              {sources?.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center gap-2">
                      <Database className="w-8 h-8 text-slate-600 mb-2" />
                      <p className="text-sm font-medium">No sources registered</p>
                      <p className="text-xs text-slate-500">Click "Add Source" to register your first intelligence feed.</p>
                      <button onClick={openCreate} className="btn-primary mt-3 text-xs">
                        <Plus className="w-3.5 h-3.5 mr-1" /> Add Source
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create/Edit Modal */}
      <SourceFormModal
        isOpen={modalOpen}
        editTarget={editTarget}
        onClose={() => { setModalOpen(false); setEditTarget(null) }}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={!!deleteTarget}
        title="Remove Source?"
        description={`Are you sure you want to remove "${deleteTarget?.name}"? This will not delete any indicators already ingested from this source.`}
        confirmText={deleteMutation.isPending ? 'Removing...' : 'Yes, Remove'}
        cancelText="Cancel"
        isDestructive={true}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => { if (deleteTarget) deleteMutation.mutate(deleteTarget.id) }}
      />
    </div>
  )
}

function PullButton({ sourceId }: { sourceId: string }) {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: () => pullSource(sourceId),
    onSuccess: (data) => {
      toast.success(data.message || `Pulled successfully! ${data.ingested} new indicators.`)
      queryClient.invalidateQueries({ queryKey: ['sources'] })
      queryClient.invalidateQueries({ queryKey: ['indicators'] })
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      toast.error(`Failed to pull feed: ${msg}`)
    },
  })

  return (
    <button
      title="Pull feed now"
      onClick={() => mutation.mutate()}
      disabled={mutation.isPending}
      className="p-1.5 rounded text-slate-500 hover:text-green-400 hover:bg-green-500/10 transition-colors disabled:opacity-50"
    >
      <RefreshCw className={clsx("w-3.5 h-3.5", mutation.isPending && "animate-spin")} />
    </button>
  )
}

export function SourcesPage() {
  return (
    <PageErrorBoundary>
      <SourcesContent />
    </PageErrorBoundary>
  )
}

