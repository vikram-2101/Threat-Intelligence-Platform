/**
 * TypeScript interfaces that mirror the backend Pydantic schemas.
 * Agent.md §12: "All API types are in /src/types/. Mirror the backend Pydantic schemas.
 * When the backend schema changes, update the TypeScript type in the same commit."
 *
 * No `any` types allowed — use `unknown` with type guards if shape is uncertain.
 */

// ── Enums ──────────────────────────────────────────────────────────────────────

export type IndicatorType = 'IPV4' | 'IPV6' | 'DOMAIN' | 'URL' | 'MD5' | 'SHA1' | 'SHA256'

export type IndicatorStatus = 'ACTIVE' | 'EXPIRED' | 'REVOKED'

export type EvidenceType =
  | 'WHOIS'
  | 'PASSIVE_DNS'
  | 'ASN'
  | 'SSL_CERT'
  | 'CORRELATION_INFRA'
  | 'CORRELATION_SSL'
  | 'MULTI_SOURCE_SIGHTING'
  | 'ANALYST_NOTE'
  | 'ANALYST_ADJUSTMENT'
  | 'REVOCATION'

export type TrustTier = 'LOW' | 'MEDIUM' | 'HIGH'

export type SourceCategory = 'community' | 'research' | 'commercial' | 'internal'

// ── Rationale (Agent.md §7 — every snapshot must conform) ─────────────────────

export interface RationaleFactor {
  type: EvidenceType | 'ENRICHMENT_DEPTH_BONUS'
  delta: number
  weight?: number
  contribution?: number
  evidence_id: string | null
  source_name: string
}

export interface Rationale {
  score: number
  base_score?: number
  enrichment_depth_bonus?: number
  correlation_bonus?: number
  analyst_adjustment?: number
  weighted_sum: number
  decay_factor: number
  days_elapsed: number
  calculated_at: string
  factors: RationaleFactor[]
}

// ── Evidence ───────────────────────────────────────────────────────────────────

export interface Evidence {
  id: string
  evidence_type: EvidenceType
  timestamp: string
  confidence_delta: number
  raw_payload: Record<string, unknown>
  reversible: boolean
  reversed: boolean
  reversed_at: string | null
}

// ── Confidence Snapshot ────────────────────────────────────────────────────────

export interface ConfidenceSnapshot {
  id: string
  score: number
  reason_summary: Rationale
  calculated_at: string
  trigger: string
}

// ── Indicator (lean — list view) ───────────────────────────────────────────────

export interface IndicatorListItem {
  id: string
  type: IndicatorType
  value: string
  status: IndicatorStatus
  current_confidence: number
  first_seen: string
  last_seen: string
  ttl: string
  latest_rationale: Rationale | null
  source_names: string[]
}

// ── Indicator (full detail) ────────────────────────────────────────────────────

export interface IndicatorDetail {
  id: string
  type: IndicatorType
  value: string
  status: IndicatorStatus
  current_confidence: number
  first_seen: string
  last_seen: string
  ttl: string
  evidence: Evidence[]
  confidence_history: ConfidenceSnapshot[]
  latest_rationale: Rationale | null
  source_names: string[]
}

// ── Correlation ────────────────────────────────────────────────────────────────

export interface CorrelationDetail {
  evidence_id: string
  correlation_type: EvidenceType
  confidence_delta: number
  raw_payload: Record<string, unknown>
  timestamp: string
  reversed: boolean
}

export interface CorrelationResponse {
  indicator_id: string
  correlations: CorrelationDetail[]
  total: number
}

// ── Paginated list response (Agent.md §9 envelope) ────────────────────────────

export interface PaginatedMeta {
  total: number
  page: number
  limit: number
  pages: number
}

export interface PaginatedResponse<T> {
  data: T[]
  meta: PaginatedMeta
  errors: string[]
}

// ── Source ─────────────────────────────────────────────────────────────────────

export interface Source {
  id: string
  name: string
  category: SourceCategory
  trust_tier: TrustTier
  default_weight: number
  intent_description: string | null
  pull_url: string | null
  pull_schedule: string | null
  last_pull_at: string | null
  last_pull_status: string | null
  last_pull_error: string | null
  is_active: boolean
  created_at: string
}


/** Mirrors backend SourceCreate (SourceBase) */
export interface SourceCreate {
  name: string
  category: SourceCategory
  trust_tier: TrustTier
  default_weight: number
  intent_description?: string
  pull_url?: string
  pull_schedule?: string
  is_active: boolean
}

/** Mirrors backend SourceUpdate (all optional PATCH fields) */
export interface SourceUpdate {
  name?: string
  category?: SourceCategory
  trust_tier?: TrustTier
  default_weight?: number
  intent_description?: string
  pull_url?: string
  pull_schedule?: string
  is_active?: boolean
}

// ── Auth ───────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
}

// ── Analyst action responses ───────────────────────────────────────────────────

export interface NoteResponse {
  evidence_id: string
  indicator_id: string
  note: string
  created_at: string
  message: string
}

export interface ConfidenceAdjustResponse {
  evidence_id: string
  indicator_id: string
  old_score: number
  new_score: number
  delta_applied: number
  message: string
}

export interface RevokeResponse {
  evidence_id: string
  indicator_id: string
  new_status: string
  new_score: number
  message: string
}

export interface TTLAdjustResponse {
  indicator_id: string
  old_ttl: string
  new_ttl: string
  message: string
}

// ── Filter params ─────────────────────────────────────────────────────────────

export interface IndicatorFilters {
  type?: IndicatorType
  status?: IndicatorStatus
  confidence_min?: number
  confidence_max?: number
  source?: string
  value?: string
  page?: number
  limit?: number
}
