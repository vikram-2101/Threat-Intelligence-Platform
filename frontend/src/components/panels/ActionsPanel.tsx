import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings2, ShieldAlert, MessageSquare, Clock, ArrowUpCircle, ArrowDownCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import * as Slider from '@radix-ui/react-slider'

import { addNote, adjustConfidence, adjustTTL, revokeIndicator } from '@/api/indicators'
import { ConfirmationModal } from '@/components/ConfirmationModal'
import type { IndicatorDetail } from '@/types'

interface Props {
  indicator: IndicatorDetail
}

export function ActionsPanel({ indicator }: Props) {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const indicatorId = id!

  // Form states
  const [noteText, setNoteText] = useState('')
  const [confDirection, setConfDirection] = useState<'promote' | 'demote'>('promote')
  const [confDelta, setConfDelta] = useState<number[]>([10])
  const [confReason, setConfReason] = useState('')
  
  // Expiry state (default to current TTL formatted for HTML datetime-local: YYYY-MM-DDThh:mm)
  const defaultTTL = new Date(indicator.ttl).toISOString().slice(0, 16)
  const [ttlDate, setTtlDate] = useState(defaultTTL)

  // Revoke state
  const [revokeModalOpen, setRevokeModalOpen] = useState(false)
  const [revokeReason, setRevokeReason] = useState('')

  // ───────────────────────────────────────────────────────────────────────────
  // Mutations
  // ───────────────────────────────────────────────────────────────────────────

  const handleSuccess = (message: string) => {
    toast.success(message)
    queryClient.invalidateQueries({ queryKey: ['indicator', indicatorId] })
  }

  const handleError = (error: unknown, action: string) => {
    const msg = error instanceof Error ? error.message : 'Unknown error'
    toast.error(`Failed to ${action}: ${msg}`)
  }

  // 1. Add Note
  const noteMutation = useMutation({
    mutationFn: () => addNote(indicatorId, noteText),
    onSuccess: () => {
      handleSuccess('Note added successfully')
      setNoteText('')
    },
    onError: (err) => handleError(err, 'add note')
  })

  // 2. Adjust Confidence
  const confMutation = useMutation({
    mutationFn: () => adjustConfidence(indicatorId, confDirection, confDelta[0], confReason),
    onSuccess: () => {
      handleSuccess('Confidence adjusted successfully')
      setConfReason('')
      setConfDelta([10])
    },
    onError: (err) => handleError(err, 'adjust confidence')
  })

  // 3. Adjust TTL
  const ttlMutation = useMutation({
    mutationFn: () => adjustTTL(indicatorId, new Date(ttlDate).toISOString()),
    onSuccess: () => handleSuccess('Expiry date updated'),
    onError: (err) => handleError(err, 'adjust TTL')
  })

  // 4. Revoke Indicator
  const revokeMutation = useMutation({
    mutationFn: () => revokeIndicator(indicatorId, revokeReason),
    onSuccess: () => {
      handleSuccess('Indicator has been formally revoked')
      setRevokeModalOpen(false)
      setRevokeReason('')
    },
    onError: (err) => handleError(err, 'revoke indicator')
  })

  const isRevoked = indicator.status === 'REVOKED'

  return (
    <>
      <div className="card h-full flex flex-col relative overflow-hidden">
        {isRevoked && (
          <div className="absolute inset-0 bg-surface-900/60 backdrop-blur-[2px] z-20 flex flex-col items-center justify-center text-center p-6">
            <ShieldAlert className="w-12 h-12 text-red-500/50 mb-3" />
            <h3 className="text-lg font-bold text-slate-200">Indicator Revoked</h3>
            <p className="text-sm text-slate-400 max-w-sm mt-1">
              Further analyst interactions are locked on this indicator since it has been revoked. Re-verify source ingestion if activation is required.
            </p>
          </div>
        )}

        <div className="px-5 py-4 border-b border-slate-700/50 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <Settings2 className="w-4 h-4 text-brand-400" />
            <h2 className="text-sm font-semibold text-slate-200">Analyst Controls</h2>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5 scrollbar-thin space-y-8">
          
          {/* Notes Section */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare className="w-4 h-4 text-slate-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Observation Notes</h3>
            </div>
            <textarea
              className="input text-sm min-h-[80px] resize-none mb-2"
              placeholder="Add an analyst hypothesis or contextual observation..."
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
            />
            <button 
              className="btn-primary w-full text-sm py-1.5"
              disabled={!noteText.trim() || noteMutation.isPending}
              onClick={() => noteMutation.mutate()}
            >
              {noteMutation.isPending ? 'Saving...' : 'Append Note'}
            </button>
          </section>

          {/* Confidence Adjustment */}
          <section className="border-t border-slate-700/50 pt-6">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Confidence Override</h3>
              <span className="text-[10px] bg-brand-500/10 text-brand-400 px-1.5 py-0.5 rounded uppercase font-bold tracking-wider">
                Rescores Instantly
              </span>
            </div>
            
            <div className="flex bg-surface-950 p-1 rounded-lg border border-slate-800 mb-4">
              <button
                className={`flex-1 flex justify-center items-center gap-2 py-1.5 text-xs font-bold rounded-md transition-colors ${
                  confDirection === 'promote' ? 'bg-brand-500 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => setConfDirection('promote')}
              >
                <ArrowUpCircle className="w-3.5 h-3.5" /> Promote
              </button>
              <button
                className={`flex-1 flex justify-center items-center gap-2 py-1.5 text-xs font-bold rounded-md transition-colors ${
                  confDirection === 'demote' ? 'bg-orange-500 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
                onClick={() => setConfDirection('demote')}
              >
                <ArrowDownCircle className="w-3.5 h-3.5" /> Demote
              </button>
            </div>

            <div className="mb-4">
              <div className="flex justify-between text-xs mb-2">
                <span className="text-slate-400">Score Delta</span>
                <span className="font-mono font-bold text-slate-200">{confDirection === 'promote' ? '+' : '-'}{confDelta[0]}</span>
              </div>
              <Slider.Root
                className="relative flex w-full touch-none select-none items-center h-5"
                min={0}
                max={50}
                value={confDelta}
                onValueChange={setConfDelta}
                step={5}
              >
                <Slider.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-surface-700">
                  <Slider.Range className={`absolute h-full ${confDirection === 'promote' ? 'bg-brand-500' : 'bg-orange-500'}`} />
                </Slider.Track>
                <Slider.Thumb className={`block h-4 w-4 rounded-full border shadow transition-colors focus-visible:outline-none focus-visible:ring-2 bg-white ${confDirection === 'promote' ? 'border-brand-500 focus-visible:ring-brand-500/50' : 'border-orange-500 focus-visible:ring-orange-500/50'}`} />
              </Slider.Root>
            </div>

            <input
              type="text"
              className="input text-sm mb-2"
              placeholder="Mandatory reasoning..."
              value={confReason}
              onChange={(e) => setConfReason(e.target.value)}
            />
            <button 
              className="btn-secondary w-full text-sm py-1.5"
              disabled={!confReason.trim() || confMutation.isPending}
              onClick={() => confMutation.mutate()}
            >
              {confMutation.isPending ? 'Calculating...' : 'Commit Adjustment'}
            </button>
          </section>

          {/* Expiry Override */}
          <section className="border-t border-slate-700/50 pt-6">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-4 h-4 text-slate-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Set Expiry (TTL)</h3>
            </div>
            <div className="flex gap-2">
              <input
                type="datetime-local"
                className="input text-sm flex-1"
                value={ttlDate}
                onChange={(e) => setTtlDate(e.target.value)}
              />
              <button 
                className="btn-secondary px-4 text-sm"
                disabled={ttlMutation.isPending || ttlDate === defaultTTL}
                onClick={() => ttlMutation.mutate()}
              >
                Save
              </button>
            </div>
          </section>

          {/* Revocation */}
          <section className="border-t border-slate-700/50 pt-6">
            <button 
              className="btn-danger w-full py-2 bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20"
              onClick={() => setRevokeModalOpen(true)}
            >
              Revoke Indicator...
            </button>
          </section>
        </div>
      </div>

      {/* Revocation Guard Modal */}
      <ConfirmationModal
        isOpen={revokeModalOpen}
        title="Revoke Indicator?"
        description="Are you absolutely sure you want to revoke this indicator? This action cannot be easily undone, locks the indicator from further updates, and severely penalizes the confidence score."
        confirmText={revokeMutation.isPending ? "Revoking..." : "Yes, Revoke"}
        cancelText="Cancel"
        isDestructive={true}
        onCancel={() => {
          setRevokeModalOpen(false)
          setRevokeReason('')
        }}
        onConfirm={() => {
          if (revokeReason.trim() === '') {
            toast.error('A mandatory justification is required.')
            return
          }
          revokeMutation.mutate()
        }}
      >
        <div className="mt-2">
          <label className="block text-xs uppercase tracking-wider font-bold text-slate-400 mb-2">
            Justification (Required)
          </label>
          <input
            type="text"
            className="input"
            autoFocus
            placeholder="e.g., False positive confirmed by IR team"
            value={revokeReason}
            onChange={(e) => setRevokeReason(e.target.value)}
          />
        </div>
      </ConfirmationModal>
    </>
  )
}
