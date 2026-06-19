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
    
    // Create a temporary link with auth header
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

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setParams({
      ...params,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 10,
    })
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
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => navigate('/employees/new')}
                >
                  添加员工
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
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
    </div>
  )
}

export default EmployeeList
