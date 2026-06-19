import { useEffect, useState } from 'react'
import {
  Table,
  Button,
  Select,
  Space,
  Tag,
  Card,
  Row,
  Col,
  DatePicker,
  Typography,
  Drawer,
  Descriptions,
} from 'antd'
import { SearchOutlined, EyeOutlined } from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import {
  auditLogApi,
  AuditLog,
  AuditActionType,
  AUDIT_ACTION_LABELS,
  AuditLogListParams,
} from '../api/auditLog'
import dayjs, { Dayjs } from 'dayjs'

const { Option } = Select
const { Text, Paragraph } = Typography
const { RangePicker } = DatePicker

const ACTION_COLORS: Record<AuditActionType, string> = {
  create: 'green',
  update: 'blue',
  delete: 'red',
  bulk_update_status: 'orange',
  bulk_delete: 'volcano',
  csv_import: 'purple',
}

const AuditLogList = () => {
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [total, setTotal] = useState(0)
  const [detailVisible, setDetailVisible] = useState(false)
  const [currentLog, setCurrentLog] = useState<AuditLog | null>(null)
  const [params, setParams] = useState<AuditLogListParams>({
    page: 1,
    page_size: 10,
    action_type: undefined,
    start_date: undefined,
    end_date: undefined,
  })

  useEffect(() => {
    loadLogs()
  }, [params])

  const loadLogs = async () => {
    setLoading(true)
    try {
      const response = await auditLogApi.getList(params)
      setLogs(response.items)
      setTotal(response.total)
    } catch {
      // Error handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  const handleTableChange = (pagination: TablePaginationConfig) => {
    setParams({
      ...params,
      page: pagination.current || 1,
      page_size: pagination.pageSize || 10,
    })
  }

  const handleDateRangeChange = (dates: [Dayjs | null, Dayjs | null] | null) => {
    setParams({
      ...params,
      page: 1,
      start_date: dates?.[0]?.format('YYYY-MM-DD'),
      end_date: dates?.[1]?.format('YYYY-MM-DD'),
    })
  }

  const handleReset = () => {
    setParams({
      page: 1,
      page_size: 10,
      action_type: undefined,
      start_date: undefined,
      end_date: undefined,
    })
  }

  const showDetail = (log: AuditLog) => {
    setCurrentLog(log)
    setDetailVisible(true)
  }

  const formatDetail = (detail: Record<string, unknown> | null) => {
    if (!detail) return <Text type="secondary">无详细信息</Text>
    return (
      <pre
        style={{
          background: '#f5f5f5',
          padding: 12,
          borderRadius: 4,
          fontSize: 12,
          maxHeight: 400,
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
        }}
      >
        {JSON.stringify(detail, null, 2)}
      </pre>
    )
  }

  const columns: ColumnsType<AuditLog> = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作类型',
      dataIndex: 'action_type',
      key: 'action_type',
      width: 120,
      render: (action: AuditActionType) => (
        <Tag color={ACTION_COLORS[action]}>
          {AUDIT_ACTION_LABELS[action]}
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
      width: 150,
      render: (_, record) => {
        const detail = record.action_detail as Record<string, unknown> | null
        if (record.action_type === 'csv_import') {
          return <Text type="secondary">批量导入</Text>
        }
        if (record.action_type.startsWith('bulk_')) {
          const count = (detail?.success_count as number) || 0
          return <Text type="secondary">共 {count} 条记录</Text>
        }
        const name = detail?.name as string
        const empId = detail?.employee_id as string
        return name ? `${name}${empId ? ` (${empId})` : ''}` : record.target_id || '-'
      },
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 140,
      render: (ip: string | null) => ip || '-',
    },
    {
      title: '操作摘要',
      key: 'summary',
      ellipsis: true,
      render: (_, record) => {
        const detail = record.action_detail as Record<string, unknown> | null
        if (!detail) return '-'

        if (record.action_type === 'create') {
          const changes = detail.changes as Record<string, any> | undefined
          const after = changes?.after as Record<string, any> | undefined
          return `新增员工：${detail.name || ''}，邮箱：${after?.email || ''}`
        }
        if (record.action_type === 'update') {
          const changes = detail.changes as Record<string, unknown>
          if (changes) {
            const changedFields = Object.keys(changes).join('、')
            return `修改字段：${changedFields}`
          }
          return '修改员工信息'
        }
        if (record.action_type === 'delete') {
          return `删除员工：${detail.name || ''}`
        }
        if (record.action_type === 'bulk_update_status') {
          return `批量改状态为${detail.target_status === 'active' ? '在职' : '离职'}，成功 ${detail.success_count} 人`
        }
        if (record.action_type === 'bulk_delete') {
          return `批量删除员工，成功 ${detail.success_count} 人`
        }
        if (record.action_type === 'csv_import') {
          return `CSV导入：成功 ${detail.success_count} 条，失败 ${detail.failed_count} 条`
        }
        return '-'
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => showDetail(record)}
        >
          详情
        </Button>
      ),
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
              value={params.action_type}
              onChange={(value) =>
                setParams({ ...params, action_type: value, page: 1 })
              }
            >
              {Object.entries(AUDIT_ACTION_LABELS).map(([key, label]) => (
                <Option key={key} value={key}>
                  {label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              style={{ width: '100%' }}
              value={
                params.start_date && params.end_date
                  ? [dayjs(params.start_date), dayjs(params.end_date)]
                  : null
              }
              onChange={handleDateRangeChange}
            />
          </Col>
          <Col xs={24} sm={12} md={10} style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={handleReset}>重置</Button>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={loadLogs}
              >
                查询
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
          scroll={{ x: 1000 }}
          pagination={{
            current: params.page,
            pageSize: params.page_size,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 条记录`,
          }}
          onChange={handleTableChange}
        />
      </Card>

      <Drawer
        title="操作详情"
        width={640}
        open={detailVisible}
        onClose={() => setDetailVisible(false)}
      >
        {currentLog && (
          <>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="操作时间">
                {dayjs(currentLog.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="操作类型">
                <Tag color={ACTION_COLORS[currentLog.action_type]}>
                  {AUDIT_ACTION_LABELS[currentLog.action_type]}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="操作人">
                {currentLog.operator_name} (ID: {currentLog.operator_id})
              </Descriptions.Item>
              <Descriptions.Item label="IP地址">
                {currentLog.ip_address || '未知'}
              </Descriptions.Item>
              <Descriptions.Item label="目标ID">
                {currentLog.target_id || '-'}
              </Descriptions.Item>
            </Descriptions>
            <div style={{ marginTop: 16 }}>
              <Paragraph strong>变更详情：</Paragraph>
              {formatDetail(currentLog.action_detail)}
            </div>
          </>
        )}
      </Drawer>
    </div>
  )
}

export default AuditLogList
