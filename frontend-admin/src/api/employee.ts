import request from './request'

export type Gender = 'male' | 'female'
export type EmployeeStatus = 'active' | 'inactive'

export interface Employee {
  id: number
  employee_id: string
  name: string
  gender: Gender
  age: number
  department: string
  position: string
  email: string
  phone: string | null
  hire_date: string
  status: EmployeeStatus
  created_at: string
  updated_at: string | null
}

export interface EmployeeListParams {
  page?: number
  page_size?: number
  search?: string
  department?: string
  status?: EmployeeStatus
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface EmployeeListResponse {
  items: Employee[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface CreateEmployeeParams {
  name: string
  gender: Gender
  age: number
  department: string
  position: string
  email: string
  phone?: string
  hire_date: string
  status?: EmployeeStatus
}

export interface UpdateEmployeeParams {
  name?: string
  gender?: Gender
  age?: number
  department?: string
  position?: string
  email?: string
  phone?: string
  hire_date?: string
  status?: EmployeeStatus
}

export interface Statistics {
  total: number
  active: number
  inactive: number
  this_month_hires: number
  active_rate: number
  gender_distribution: {
    male: number
    female: number
  }
  department_distribution: Array<{
    department: string
    count: number
  }>
  hire_trend: Array<{
    month: string
    count: number
  }>
}

export interface BatchOperationError {
  id?: number
  row?: number
  message: string
}

export interface BatchOperationResponse {
  success_count: number
  failed_count: number
  errors: BatchOperationError[]
}

export interface CsvImportRowResult {
  row: number
  success: boolean
  message?: string
  employee_id?: string
}

export interface CsvImportResponse {
  success_count: number
  failed_count: number
  total_count: number
  results: CsvImportRowResult[]
}

export const employeeApi = {
  getList: (params: EmployeeListParams): Promise<EmployeeListResponse> => {
    return request.get('/employees', { params })
  },

  getById: (id: number): Promise<Employee> => {
    return request.get(`/employees/${id}`)
  },

  create: (data: CreateEmployeeParams): Promise<Employee> => {
    return request.post('/employees', data)
  },

  update: (id: number, data: UpdateEmployeeParams): Promise<Employee> => {
    return request.put(`/employees/${id}`, data)
  },

  delete: (id: number): Promise<void> => {
    return request.delete(`/employees/${id}`)
  },

  getDepartments: (): Promise<{ departments: string[] }> => {
    return request.get('/employees/departments')
  },

  getStatistics: (): Promise<Statistics> => {
    return request.get('/employees/statistics')
  },

  exportCsv: (params?: EmployeeListParams): string => {
    const searchParams = new URLSearchParams()
    if (params?.search) searchParams.append('search', params.search)
    if (params?.department) searchParams.append('department', params.department)
    if (params?.status) searchParams.append('status', params.status)
    return `/api/employees/export?${searchParams.toString()}`
  },

  batchUpdateStatus: (ids: number[], status: EmployeeStatus): Promise<BatchOperationResponse> => {
    return request.post('/employees/batch/status', { ids, status })
  },

  batchDelete: (ids: number[]): Promise<BatchOperationResponse> => {
    return request.post('/employees/batch/delete', { ids })
  },

  importCsv: (file: File): Promise<CsvImportResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/employees/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
