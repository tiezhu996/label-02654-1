import request from './request'

export type AuditActionType =
  | 'create'
  | 'update'
  | 'delete'
  | 'batch_update_status'
  | 'batch_delete'
  | 'import'

export interface AuditLog {
  id: number
  action_type: AuditActionType
  operator_id: number
  operator_name: string
  target_ids: number[] | null
  target_name: string | null
  changes: Record<string, { old: unknown; new: unknown }> | null
  details: string | null
  created_at: string
}

export interface AuditLogListParams {
  page?: number
  page_size?: number
  action_type?: AuditActionType
  start_date?: string
  end_date?: string
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
