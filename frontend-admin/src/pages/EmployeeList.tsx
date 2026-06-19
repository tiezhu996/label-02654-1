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
  Dropdown,
  Upload,
} from 'antd'
import type { MenuProps } from 'antd'
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
  DownOutlined,
} from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import {
  employeeApi,
  Employee,
  EmployeeStatus,
  EmployeeListParams,
} from '../api/employee'
import { useAuthStore } from '../stores/authStore'
import type { UploadProps } from 'antd'

const { Option } = Select

const EmployeeList = () => {
  const navigate = useNavigate()
  const { isAdmin } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [employees, setEmployees] = useState<Employee[]>([])
  const [total, setTotal] = useState(0)
  const [departments, setDepartments] = useState<string[]>([])
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])
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

  useEffect(() => {
    setSelectedRowKeys([])
  }, [params.page, params.page_size, params.search, params.department, params.status])

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

  const handleBulkStatusUpdate = (targetStatus: EmployeeStatus) => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要操作的员工')
      return
    }

    const ids = selectedRowKeys as number[]
    const inactiveSelected = employees.filter(
      (e) => ids.includes(e.id) && e.status === 'inactive'
    )

    const statusText = targetStatus === 'active' ? '在职' : '离职'

    let content = `确定要将选中的 ${ids.length} 名员工状态修改为"${statusText}"吗？`
    if (targetStatus === 'inactive' && inactiveSelected.length > 0) {
      content += `\n\n注意：已选中的 ${inactiveSelected.length} 名离职员工将被跳过（不允许批量变更已离职员工状态）。`
    }

    Modal.confirm({
      title: `批量修改状态为"${statusText}"`,
      content,
      okText: '确认修改',
      okType: 'primary',
      cancelText: '取消',
      onOk: async () => {
        try {
          const result = await employeeApi.bulkUpdateStatus(ids, targetStatus)
          message.success(result.message)
          setSelectedRowKeys([])
          loadEmployees()
        } catch {
          // Error handled by interceptor
        }
      },
    })
  }

  const handleBulkDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的员工')
      return
    }

    Modal.confirm({
      title: '批量删除确认',
      content: `确定要删除选中的 ${selectedRowKeys.length} 名员工吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const result = await employeeApi.bulkDelete(selectedRowKeys as number[])
          message.success(result.message)
          setSelectedRowKeys([])
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

  const uploadProps: UploadProps = {
    accept: '.csv',
    showUploadList: false,
    beforeUpload: async (file) => {
      try {
        message.loading({ content: '正在导入...', key: 'import' })
        const result = await employeeApi.importCsv(file)
        message.destroy('import')

        const { success_count, failed_count, errors } = result
        if (failed_count === 0) {
          message.success(`导入成功！共导入 ${success_count} 条记录`)
        } else if (success_count > 0) {
          message.warning(`导入完成：成功 ${success_count} 条，失败 ${failed_count} 条`)
          Modal.info({
            title: '导入结果详情',
            width: 600,
            content: (
              <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                <p>
                  成功：<strong style={{ color: '#52c41a' }}>{success_count} 条</strong>，
                  失败：<strong style={{ color: '#ff4d4f' }}>{failed_count} 条</strong>
                </p>
                {errors.length > 0 && (
                  <div>
                    <p><strong>失败详情：</strong></p>
                    <ul style={{ paddingLeft: 20 }}>
                      {errors.map((e, i) => (
                        <li key={i} style={{ color: '#ff4d4f', marginBottom: 4 }}>
                          第 {e.row} 行：{e.message}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ),
          })
        } else {
          message.error(`导入失败：共 ${failed_count} 条记录出错`)
          Modal.error({
            title: '导入失败详情',
            width: 600,
            content: (
              <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                <ul style={{ paddingLeft: 20 }}>
                  {errors.map((e, i) => (
                    <li key={i} style={{ color: '#ff4d4f', marginBottom: 4 }}>
                      第 {e.row} 行：{e.message}
                    </li>
                  ))}
                </ul>
              </div>
            ),
          })
        }
        loadEmployees()
      } catch {
        message.destroy('import')
        // Error handled by interceptor
      }
      return false
    },
  }

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setParams({
      ...params,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 10,
    })
  }

  const bulkActionMenu: MenuProps['items'] = [
    {
      key: 'setActive',
      label: '设为在职',
      disabled: selectedRowKeys.length === 0,
      onClick: () => handleBulkStatusUpdate('active'),
    },
    {
      key: 'setInactive',
      label: '设为离职',
      disabled: selectedRowKeys.length === 0,
      onClick: () => handleBulkStatusUpdate('inactive'),
    },
    {
      type: 'divider',
    },
    {
      key: 'bulkDelete',
      label: <span style={{ color: '#ff4d4f' }}>批量删除</span>,
      disabled: selectedRowKeys.length === 0,
      onClick: handleBulkDelete,
    },
  ]

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

  const rowSelection = isAdmin
    ? {
        selectedRowKeys,
        onChange: (newSelectedRowKeys: React.Key[]) => {
          setSelectedRowKeys(newSelectedRowKeys)
        },
        getCheckboxProps: (record: Employee) => ({
          disabled: false,
          name: record.name,
        }),
      }
    : undefined

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
                  <Upload {...uploadProps}>
                    <Button icon={<ImportOutlined />}>导入 CSV</Button>
                  </Upload>
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
        <Card
          style={{
            marginBottom: 16,
            background: '#e6f4ff',
            border: '1px solid #91caff',
          }}
        >
          <Row align="middle" justify="space-between">
            <Col>
              <Space>
                <span>已选择 <strong>{selectedRowKeys.length}</strong> 项</span>
                <Button
                  type="link"
                  size="small"
                  onClick={() => setSelectedRowKeys([])}
                >
                  取消选择
                </Button>
              </Space>
            </Col>
            <Col>
              <Dropdown menu={{ items: bulkActionMenu }}>
                <Button type="primary">
                  批量操作 <DownOutlined />
                </Button>
              </Dropdown>
            </Col>
          </Row>
        </Card>
      )}

      <Card>
        <Table
          rowSelection={rowSelection}
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
