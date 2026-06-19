import request from './request'

export type AuditAction =
  | 'create'
  | 'update'
  | 'delete'
  | 'bulk_update'
  | 'bulk_delete'
  | 'import'

export interface AuditLog {
  id: number
  action: AuditAction
  operator_id: number
  operator_name: string
  target_type: string
  target_id: string | null
  target_name: string | null
  changes: Record<string, unknown> | null
  summary: string | null
  created_at: string
}

export interface AuditLogListParams {
  page?: number
  page_size?: number
  action?: AuditAction
  start_time?: string
  end_time?: string
}

export interface AuditLogListResponse {
  items: AuditLog[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const auditLogApi = {
  getList: (params: AuditLogListParams): Promise<AuditLogListResponse> => {
    return request.get('/audit-logs', { params })
  },
}
