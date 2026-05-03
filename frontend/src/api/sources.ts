/**
 * Sources API query/mutation functions.
 * Agent.md §12: "src/api/ — one file per resource"
 *
 * Unwraps the standard response envelope where applicable.
 */

import api from '@/lib/axios'
import type { Source, SourceCreate, SourceUpdate } from '@/types'

// ── Read queries ───────────────────────────────────────────────────────────────

/** GET /api/v1/sources — list all sources (ANALYST + ADMIN) */
export const getSources = async (): Promise<Source[]> => {
  const { data } = await api.get<Source[]>('sources/')
  return data
}

/** GET /api/v1/sources/{id} */
export const getSource = async (id: string): Promise<Source> => {
  const { data } = await api.get<Source>(`sources/${id}`)
  return data
}

// ── Mutations (ADMIN only — enforced server-side) ─────────────────────────────

/** POST /api/v1/sources — create a new intelligence source */
export const createSource = async (payload: SourceCreate): Promise<Source> => {
  const { data } = await api.post<Source>('sources/', payload)
  return data
}

/** PATCH /api/v1/sources/{id} — update an existing source */
export const updateSource = async (id: string, payload: SourceUpdate): Promise<Source> => {
  const { data } = await api.patch<Source>(`sources/${id}`, payload)
  return data
}

/** DELETE /api/v1/sources/{id} — remove a source (204, no body) */
export const deleteSource = async (id: string): Promise<void> => {
  await api.delete(`sources/${id}`)
}

/** POST /api/v1/sources/{id}/pull — manually pull a source feed */
export const pullSource = async (id: string): Promise<{ message: string; ingested: number }> => {
  const { data } = await api.post<{ message: string; ingested: number }>(`sources/${id}/pull`)
  return data
}

