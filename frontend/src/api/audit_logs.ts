import { apiClient } from './auth'

export interface AuditLog {
  id: string
  user_id: string | null
  action: string
  entity_type: string | null
  entity_id: string | null
  details: any
  ip_address: string | null
  is_active: boolean
  timestamp: string
}

export interface PaginatedAuditLogs {
  data: AuditLog[]
  meta: {
    total: number
    page: number
    limit: number
    pages: number
  }
}

interface FetchAuditLogsParams {
  page?: number
  limit?: number
  action?: string
  entity_type?: string
  date_start?: string
  date_end?: string
}

export const fetchAuditLogs = async (params: FetchAuditLogsParams): Promise<PaginatedAuditLogs> => {
  const { data } = await apiClient.get('/api/v1/audit-logs', { params })
  return data
}
