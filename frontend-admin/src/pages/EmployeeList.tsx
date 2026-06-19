import { useEffect, useState } from 'react'
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
  Upload,
  Alert,
  List,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  ExportOutlined,
  ImportOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ManOutlined,
  WomanOutlined,
} from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import type { UploadProps } from 'antd'
import {
  employeeApi,
  Employee,
  EmployeeStatus,
  EmployeeListParams,
  CsvImportResponse,
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
  const [importModalVisible, setImportModalVisible] = useState(false)
  const [importResult, setImportResult] = useState<CsvImportResponse | null>(null)
  const [importing, setImporting] = useState(false)
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
    } finally {
      setLoading(false)
    }
  }

  const loadDepartments = async () => {
    try {
      const response = await employeeApi.getDepartments()
      setDepartments(response.departments)
    } catch {
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
          setSelectedRowKeys(selectedRowKeys.filter(key => key !== record.id))
          loadEmployees()
        } catch {
        }
      },
    })
  }

  const handleBatchStatusChange = (newStatus: EmployeeStatus) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择员工')
      return
    }
    const statusText = newStatus === 'active' ? '在职' : '离职'
    Modal.confirm({
      title: `批量设为${statusText}`,
      content: `确定要将选中的 ${selectedRowKeys.length} 名员工状态设为${statusText}吗？已离职员工不会被变更。`,
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          const result = await employeeApi.batchUpdateStatus(
            selectedRowKeys as number[],
            newStatus
          )
          message.success(`成功更新 ${result.success_count} 人`)
          if (result.failed_items.length > 0) {
            Modal.info({
              title: '部分员工未更新',
              content: (
                <List
                  size="small"
                  dataSource={result.failed_items}
                  renderItem={item => (
                    <List.Item>
                      {item.name || `ID: ${item.id}`}: {item.reason}
                    </List.Item>
                  )}
                />
              ),
            })
          }
          setSelectedRowKeys([])
          loadEmployees()
        } catch {
        }
      },
    })
  }

  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择员工')
      return
    }
    Modal.confirm({
      title: '批量删除',
      content: `确定要删除选中的 ${selectedRowKeys.length} 名员工吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const result = await employeeApi.batchDelete(selectedRowKeys as number[])
          message.success(`成功删除 ${result.success_count} 人`)
          if (result.failed_items.length > 0) {
            Modal.info({
              title: '部分员工未删除',
              content: (
                <List
                  size="small"
                  dataSource={result.failed_items}
                  renderItem={item => (
                    <List.Item>
                      {item.name || `ID: ${item.id}`}: {item.reason}
                    </List.Item>
                  )}
                />
              ),
            })
          }
          setSelectedRowKeys([])
          loadEmployees()
        } catch {
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
    setImportResult(null)
    setImportModalVisible(true)
  }

  const handleFileChange: UploadProps['beforeUpload'] = (file) => {
    setImporting(true)
    setImportResult(null)
    employeeApi
      .importCsv(file)
      .then((result) => {
        setImportResult(result)
        message.success(`成功导入 ${result.success_count} 人`)
        loadEmployees()
        loadDepartments()
      })
      .catch(() => {
        message.error('导入失败')
      })
      .finally(() => {
        setImporting(false)
      })
    return false
  }

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setParams({
      ...params,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 10,
    })
  }

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys)
    },
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
                  <Button icon={<ImportOutlined />} onClick={handleImportClick}>
                    导入 CSV
                  </Button>
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
            <Button size="small" onClick={() => handleBatchStatusChange('active')}>
              设为在职
            </Button>
            <Button size="small" onClick={() => handleBatchStatusChange('inactive')}>
              设为离职
            </Button>
            <Button size="small" danger onClick={handleBatchDelete}>
              批量删除
            </Button>
            <Button size="small" onClick={() => setSelectedRowKeys([])}>
              取消选择
            </Button>
          </Space>
        </Card>
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={employees}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          rowSelection={isAdmin ? rowSelection : undefined}
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
        title="导入员工数据"
        open={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        footer={null}
        width={600}
      >
        <div style={{ marginBottom: 16 }}>
          <p style={{ marginBottom: 8 }}>请选择 CSV 文件导入，格式需与导出格式一致。</p>
          <p style={{ marginBottom: 16, color: '#666', fontSize: 12 }}>
            必填字段：姓名、邮箱、部门、职位、性别、年龄、入职日期。出错的行不会阻断其他行的导入。
          </p>
          <Upload
            accept=".csv"
            showUploadList={false}
            beforeUpload={handleFileChange}
          >
            <Button icon={<ImportOutlined />} loading={importing}>
              选择文件
            </Button>
          </Upload>
        </div>

        {importResult && (
          <div>
            <Alert
              message={`导入完成：成功 ${importResult.success_count} 人，失败 ${importResult.failed_items.length} 行`}
              type={importResult.failed_items.length > 0 ? 'warning' : 'success'}
              showIcon
              style={{ marginBottom: 16 }}
            />
            {importResult.failed_items.length > 0 && (
              <List
                size="small"
                header="失败详情"
                bordered
                dataSource={importResult.failed_items}
                renderItem={(item) => (
                  <List.Item>
                    第 {item.row} 行{item.name ? ` (${item.name})` : ''}: {item.reason}
                  </List.Item>
                )}
                style={{ maxHeight: 300, overflow: 'auto' }}
              />
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default EmployeeList
