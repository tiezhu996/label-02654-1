import { useEffect, useState } from 'react'
import {
  Table,
  Select,
  Space,
  Tag,
  Card,
  Row,
  Col,
  DatePicker,
  Button,
  Typography,
} from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import type { Dayjs } from 'dayjs'
import {
  auditLogApi,
  AuditLog,
  AuditActionType,
} from '../api/auditLog'

const { Option } = Select
const { RangePicker } = DatePicker
const { Text } = Typography

const actionTypeLabels: Record<AuditActionType, string> = {
  create: '创建员工',
  update: '更新员工',
  delete: '删除员工',
  batch_update_status: '批量修改状态',
  batch_delete: '批量删除',
  import: 'CSV导入',
}

const actionTypeColors: Record<AuditActionType, string> = {
  create: 'green',
  update: 'blue',
  delete: 'red',
  batch_update_status: 'orange',
  batch_delete: 'volcano',
  import: 'purple',
}

const AuditLogList = () => {
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [total, setTotal] = useState(0)
  const [actionType, setActionType] = useState<AuditActionType | undefined>()
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null)
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 10,
  })

  useEffect(() => {
    loadLogs()
  }, [pagination, actionType, dateRange])

  const loadLogs = async () => {
    setLoading(true)
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.page_size,
        action_type: actionType,
        start_date: dateRange?.[0]?.format('YYYY-MM-DD'),
        end_date: dateRange?.[1]?.format('YYYY-MM-DD'),
      }
      const response = await auditLogApi.getList(params)
      setLogs(response.items)
      setTotal(response.total)
    } catch {
      // Error handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  const handleTableChange = (tablePagination: TablePaginationConfig) => {
    setPagination({
      page: tablePagination.current || 1,
      page_size: tablePagination.pageSize || 10,
    })
  }

  const handleReset = () => {
    setActionType(undefined)
    setDateRange(null)
    setPagination({ page: 1, page_size: 10 })
  }

  const renderChanges = (changes: AuditLog['changes']) => {
    if (!changes || Object.keys(changes).length === 0) {
      return <span style={{ color: '#999' }}>-</span>
    }
    return (
      <div>
        {Object.entries(changes).map(([field, change], idx) => (
          <div key={idx} style={{ marginBottom: 4 }}>
            <Text strong>{field}: </Text>
            <Text delete type="secondary">{String(change?.old ?? '无')}</Text>
            {' → '}
            <Text type="success">{String(change?.new ?? '无')}</Text>
          </div>
        ))}
      </div>
    )
  }

  const columns: ColumnsType<AuditLog> = [
    {
      title: '操作时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (value: string) => new Date(value).toLocaleString('zh-CN'),
    },
    {
      title: '操作类型',
      dataIndex: 'action_type',
      key: 'action_type',
      width: 140,
      render: (type: AuditActionType) => (
        <Tag color={actionTypeColors[type]}>
          {actionTypeLabels[type]}
        </Tag>
      ),
    },
    {
      title: '操作人',
      dataIndex: 'operator_name',
      key: 'operator_name',
      width: 120,
    },
    {
      title: '操作对象',
      key: 'target',
      width: 200,
      render: (_, record) => (
        <div>
          {record.target_name && <div>{record.target_name}</div>}
          {record.target_ids && record.target_ids.length > 1 && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              等 {record.target_ids.length} 人
            </Text>
          )}
        </div>
      ),
    },
    {
      title: '字段变更',
      key: 'changes',
      width: 300,
      render: (_, record) => renderChanges(record.changes),
    },
    {
      title: '详情',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
    },
  ]

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="操作类型"
              allowClear
              style={{ width: '100%' }}
              value={actionType}
              onChange={(value) => {
                setActionType(value)
                setPagination({ ...pagination, page: 1 })
              }}
              suffixIcon={<SearchOutlined />}
            >
              {Object.entries(actionTypeLabels).map(([value, label]) => (
                <Option key={value} value={value}>
                  {label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              style={{ width: '100%' }}
              value={dateRange}
              onChange={(dates) => {
                setDateRange(dates as [Dayjs | null, Dayjs | null] | null)
                setPagination({ ...pagination, page: 1 })
              }}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                重置
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1100 }}
          pagination={{
            current: pagination.page,
            pageSize: pagination.page_size,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 条记录`,
          }}
          onChange={handleTableChange}
        />
      </Card>
    </div>
  )
}

export default AuditLogList
