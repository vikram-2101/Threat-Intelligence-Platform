/**
 * Indicators API query functions.
 * Agent.md §12: "src/api/indicators.ts — one file per resource"
 *
 * Every function unwraps the backend's standard response envelope:
 * { data: ..., meta: ..., errors: [] }
 */

import api from '@/lib/axios'
import type {
  IndicatorDetail,
  IndicatorFilters,
  PaginatedResponse,
  IndicatorListItem,
  CorrelationResponse,
  NoteResponse,
  ConfidenceAdjustResponse,
  RevokeResponse,
  TTLAdjustResponse,
} from '@/types'

// ── Read queries ───────────────────────────────────────────────────────────────

/**
 * GET /api/v1/indicators?...
 * Returns paginated list with lean indicator objects.
 */
export const getIndicators = async (
  filters: IndicatorFilters = {},
): Promise<PaginatedResponse<IndicatorListItem>> => {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== undefined && v !== ''),
  )
  const { data } = await api.get<PaginatedResponse<IndicatorListItem>>('indicators/', { params })
  return data
}

/**
 * GET /api/v1/indicators/{id}
 * Full detail: indicator + evidence[] + confidence_snapshots[] + latest_rationale
 */
export const getIndicator = async (id: string): Promise<IndicatorDetail> => {
  const { data } = await api.get<IndicatorDetail>(`indicators/${id}`)
  return data
}

/**
 * GET /api/v1/indicators/{id}/correlations
 */
export const getIndicatorCorrelations = async (id: string): Promise<CorrelationResponse> => {
  const { data } = await api.get<CorrelationResponse>(`indicators/${id}/correlations`)
  return data
}

// ── Analyst actions (Phase 3.2) ────────────────────────────────────────────────

/**
 * POST /api/v1/indicators/{id}/notes
 */
export const addNote = async (id: string, note: string): Promise<NoteResponse> => {
  const { data } = await api.post<NoteResponse>(`indicators/${id}/notes`, { note })
  return data
}

/**
 * PATCH /api/v1/indicators/{id}/confidence
 */
export const adjustConfidence = async (
  id: string,
  direction: 'promote' | 'demote',
  delta: number,
  reason: string,
): Promise<ConfidenceAdjustResponse> => {
  const { data } = await api.patch<ConfidenceAdjustResponse>(`indicators/${id}/confidence`, {
    direction,
    delta,
    reason,
  })
  return data
}

/**
 * PATCH /api/v1/indicators/{id}/revoke
 */
export const revokeIndicator = async (id: string, reason: string): Promise<RevokeResponse> => {
  const { data } = await api.patch<RevokeResponse>(`indicators/${id}/revoke`, { reason })
  return data
}

/**
 * PATCH /api/v1/indicators/{id}/ttl
 */
export const adjustTTL = async (
  id: string,
  new_ttl: string,
  reason?: string,
): Promise<TTLAdjustResponse> => {
  const { data } = await api.patch<TTLAdjustResponse>(`indicators/${id}/ttl`, {
    new_ttl,
    reason,
  })
  return data
}

/**
 * DELETE /api/v1/indicators/{id}
 */
export const deleteIndicator = async (id: string): Promise<void> => {
  await api.delete(`indicators/${id}`)
}

/**
 * DELETE /api/v1/indicators
 */
export const clearIndicators = async (): Promise<void> => {
  await api.delete('indicators')
}

