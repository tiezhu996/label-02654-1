import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Table,
  Button,
  Input,
  Select,
  Space,
  Tag,
  Modal,
  message,
  Card,
  Row,
  Col,
  Alert,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  ExportOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ManOutlined,
  WomanOutlined,
  ImportOutlined,
  UserSwitchOutlined,
} from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import {
  employeeApi,
  Employee,
  EmployeeStatus,
  EmployeeListParams,
} from '../api/employee'
import { useAuthStore } from '../stores/authStore'

const { Option } = Select

const EmployeeList = () => {
  const navigate = useNavigate()
  const { isAdmin } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [employees, setEmployees] = useState<Employee[]>([])
  const [total, setTotal] = useState(0)
  const [departments, setDepartments] = useState<string[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
  const [batchModalVisible, setBatchModalVisible] = useState(false)
  const [batchAction, setBatchAction] = useState<'active' | 'inactive' | 'delete' | null>(null)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<{
    visible: boolean
    success: number
    failed: number
    errors: string[]
  } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [params, setParams] = useState<EmployeeListParams>({
    page: 1,
    page_size: 10,
    search: '',
    department: undefined,
    status: undefined,
  })

  useEffect(() => {
    loadEmployees()
    loadDepartments()
  }, [params])

  const loadEmployees = async () => {
    setLoading(true)
    try {
      const response = await employeeApi.getList(params)
      setEmployees(response.items)
      setTotal(response.total)
    } catch {
      // Error handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  const loadDepartments = async () => {
    try {
      const response = await employeeApi.getDepartments()
      setDepartments(response.departments)
    } catch {
      // Error handled by interceptor
    }
  }

  const handleDelete = (record: Employee) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除员工 "${record.name}" 吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await employeeApi.delete(record.id)
          message.success('删除成功')
          setSelectedRowKeys(selectedRowKeys.filter((key) => key !== record.id))
          loadEmployees()
        } catch {
          // Error handled by interceptor
        }
      },
    })
  }

  const handleExport = () => {
    const token = localStorage.getItem('token')
    const url = employeeApi.exportCsv(params)

    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const downloadUrl = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = downloadUrl
        a.download = 'employees.csv'
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(downloadUrl)
        message.success('导出成功')
      })
      .catch(() => {
        message.error('导出失败')
      })
  }

  const handleImportClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.csv')) {
      message.error('请选择CSV文件')
      return
    }

    setImporting(true)
    try {
      const result = await employeeApi.importCsv(file)
      const errors = result.results
        .filter((r) => !r.success)
        .map((r) => `第${r.row}行: ${r.message}`)

      setImportResult({
        visible: true,
        success: result.success_count,
        failed: result.failed_count,
        errors,
      })

      if (result.success_count > 0) {
        loadEmployees()
      }
    } catch {
      // Error handled by interceptor
    } finally {
      setImporting(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const showBatchModal = (action: 'active' | 'inactive' | 'delete') => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要操作的员工')
      return
    }
    setBatchAction(action)
    setBatchModalVisible(true)
  }

  const handleBatchConfirm = async () => {
    const ids = selectedRowKeys.map((key) => Number(key))
    try {
      if (batchAction === 'delete') {
        const result = await employeeApi.batchDelete(ids)
        message.success(`批量删除完成: 成功 ${result.success_count} 条，失败 ${result.failed_count} 条`)
        if (result.errors.length > 0) {
          Modal.error({
            title: '部分操作失败',
            content: (
              <ul style={{ maxHeight: 300, overflow: 'auto', paddingLeft: 20 }}>
                {result.errors.map((err, idx) => (
                  <li key={idx}>{err.message}</li>
                ))}
              </ul>
            ),
          })
        }
      } else if (batchAction === 'active' || batchAction === 'inactive') {
        const result = await employeeApi.batchUpdateStatus(ids, batchAction as EmployeeStatus)
        message.success(`批量修改状态完成: 成功 ${result.success_count} 条，失败 ${result.failed_count} 条`)
        if (result.errors.length > 0) {
          Modal.error({
            title: '部分操作失败',
            content: (
              <ul style={{ maxHeight: 300, overflow: 'auto', paddingLeft: 20 }}>
                {result.errors.map((err, idx) => (
                  <li key={idx}>{err.message}</li>
                ))}
              </ul>
            ),
          })
        }
      }
      setSelectedRowKeys([])
      setBatchModalVisible(false)
      loadEmployees()
    } catch {
      // Error handled by interceptor
    }
  }

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setParams({
      ...params,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 10,
    })
  }

  const onSelectChange = (newSelectedRowKeys: React.Key[]) => {
    setSelectedRowKeys(newSelectedRowKeys)
  }

  const rowSelection = {
    selectedRowKeys,
    onChange: onSelectChange,
    getCheckboxProps: (record: Employee) => ({
      disabled: !isAdmin,
    }),
  }

  const columns: ColumnsType<Employee> = [
    {
      title: '工号',
      dataIndex: 'employee_id',
      key: 'employee_id',
      width: 150,
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 100,
    },
    {
      title: '性别',
      dataIndex: 'gender',
      key: 'gender',
      width: 80,
      render: (gender: string) => (
        <span>
          {gender === 'male' ? (
            <ManOutlined style={{ color: '#1677ff', marginRight: 4 }} />
          ) : (
            <WomanOutlined style={{ color: '#ff85c0', marginRight: 4 }} />
          )}
          {gender === 'male' ? '男' : '女'}
        </span>
      ),
    },
    {
      title: '年龄',
      dataIndex: 'age',
      key: 'age',
      width: 80,
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      width: 120,
    },
    {
      title: '职位',
      dataIndex: 'position',
      key: 'position',
      width: 120,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 200,
      ellipsis: true,
    },
    {
      title: '入职日期',
      dataIndex: 'hire_date',
      key: 'hire_date',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: EmployeeStatus) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '在职' : '离职'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/employees/${record.id}`)}
          >
            查看
          </Button>
          {isAdmin && (
            <>
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => navigate(`/employees/${record.id}/edit`)}
              >
                编辑
              </Button>
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(record)}
              >
                删除
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ]

  const getBatchModalContent = () => {
    const count = selectedRowKeys.length
    if (batchAction === 'delete') {
      return `确定要删除选中的 ${count} 名员工吗？此操作不可恢复。`
    }
    if (batchAction === 'inactive') {
      return `确定要将选中的 ${count} 名员工设置为离职状态吗？已离职的员工将被跳过。`
    }
    if (batchAction === 'active') {
      return `确定要将选中的 ${count} 名员工设置为在职状态吗？`
    }
    return ''
  }

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="搜索姓名/工号/部门"
              prefix={<SearchOutlined />}
              allowClear
              value={params.search}
              onChange={(e) =>
                setParams({ ...params, search: e.target.value, page: 1 })
              }
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="部门筛选"
              allowClear
              style={{ width: '100%' }}
              value={params.department}
              onChange={(value) =>
                setParams({ ...params, department: value, page: 1 })
              }
            >
              {departments.map((dept) => (
                <Option key={dept} value={dept}>
                  {dept}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="状态筛选"
              allowClear
              style={{ width: '100%' }}
              value={params.status}
              onChange={(value) =>
                setParams({ ...params, status: value, page: 1 })
              }
            >
              <Option value="active">在职</Option>
              <Option value="inactive">离职</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={10} style={{ textAlign: 'right' }}>
            <Space>
              <Button icon={<ExportOutlined />} onClick={handleExport}>
                导出 CSV
              </Button>
              {isAdmin && (
                <>
                  <Button
                    icon={<ImportOutlined />}
                    onClick={handleImportClick}
                    loading={importing}
                  >
                    导入 CSV
                  </Button>
                  <input
                    type="file"
                    ref={fileInputRef}
                    accept=".csv"
                    style={{ display: 'none' }}
                    onChange={handleFileChange}
                  />
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => navigate('/employees/new')}
                  >
                    添加员工
                  </Button>
                </>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {isAdmin && selectedRowKeys.length > 0 && (
        <Card style={{ marginBottom: 16 }} size="small">
          <Space>
            <span>已选择 {selectedRowKeys.length} 项</span>
            <Button
              size="small"
              icon={<UserSwitchOutlined />}
              onClick={() => showBatchModal('active')}
            >
              批量设为在职
            </Button>
            <Button
              size="small"
              icon={<UserSwitchOutlined />}
              onClick={() => showBatchModal('inactive')}
            >
              批量设为离职
            </Button>
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => showBatchModal('delete')}
            >
              批量删除
            </Button>
          </Space>
        </Card>
      )}

      {importResult?.visible && (
        <Card style={{ marginBottom: 16 }} size="small">
          <Alert
            message="CSV导入完成"
            description={
              <div>
                <p>成功: {importResult.success} 条，失败: {importResult.failed} 条</p>
                {importResult.errors.length > 0 && (
                  <details>
                    <summary style={{ cursor: 'pointer', color: '#ff4d4f' }}>
                      查看失败详情
                    </summary>
                    <ul style={{ marginTop: 8, maxHeight: 200, overflow: 'auto', paddingLeft: 20 }}>
                      {importResult.errors.map((err, idx) => (
                        <li key={idx} style={{ color: '#ff4d4f' }}>{err}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            }
            type={importResult.failed > 0 ? 'warning' : 'success'}
            showIcon
            closable
            onClose={() => setImportResult(null)}
          />
        </Card>
      )}

      <Card>
        <Table
          rowSelection={isAdmin ? rowSelection : undefined}
          columns={columns}
          dataSource={employees}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            current: params.page,
            pageSize: params.page_size,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          onChange={handleTableChange}
        />
      </Card>

      <Modal
        title="确认批量操作"
        open={batchModalVisible}
        onOk={handleBatchConfirm}
        onCancel={() => setBatchModalVisible(false)}
        okText="确认"
        cancelText="取消"
        okType={batchAction === 'delete' ? 'danger' : 'primary'}
      >
        <p>{getBatchModalContent()}</p>
      </Modal>
    </div>
  )
}

export default EmployeeList
