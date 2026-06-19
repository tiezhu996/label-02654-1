import request from './request'

export type AuditActionType =
  | 'create'
  | 'update'
  | 'delete'
  | 'bulk_update_status'
  | 'bulk_delete'
  | 'csv_import'

export type AuditTargetType = 'employee'

export interface AuditLog {
  id: number
  action_type: AuditActionType
  target_type: AuditTargetType
  target_id: string | null
  operator_id: number
  operator_name: string
  action_detail: Record<string, unknown> | null
  ip_address: string | null
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
  getList: (params?: AuditLogListParams): Promise<AuditLogListResponse> => {
    return request.get('/audit-logs', { params })
  },
}

export const AUDIT_ACTION_LABELS: Record<AuditActionType, string> = {
  create: '新增员工',
  update: '修改员工',
  delete: '删除员工',
  bulk_update_status: '批量改状态',
  bulk_delete: '批量删除',
  csv_import: 'CSV导入',
}
