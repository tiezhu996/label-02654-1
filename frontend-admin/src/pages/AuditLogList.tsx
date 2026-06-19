import { useEffect, useState } from 'react'
import {
  Table,
  Card,
  Row,
  Col,
  Select,
  DatePicker,
  Space,
  Tag,
  Button,
  Typography,
} from 'antd'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import dayjs, { Dayjs } from 'dayjs'
import {
  auditLogApi,
  AuditLog,
  AuditActionType,
  AuditLogListParams,
} from '../api/employee'

const { Option } = Select
const { RangePicker } = DatePicker
const { Text } = Typography

const actionTypeLabels: Record<AuditActionType, { text: string; color: string }> = {
  create: { text: '创建', color: 'green' },
  update: { text: '更新', color: 'blue' },
  delete: { text: '删除', color: 'red' },
  batch_update_status: { text: '批量改状态', color: 'purple' },
  batch_delete: { text: '批量删除', color: 'volcano' },
  csv_import: { text: 'CSV导入', color: 'cyan' },
}

const AuditLogList = () => {
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [total, setTotal] = useState(0)
  const [params, setParams] = useState<AuditLogListParams>({
    page: 1,
    page_size: 10,
    action_type: undefined,
    start_date: undefined,
    end_date: undefined,
  })
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null)

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

  const handleActionTypeChange = (value: AuditActionType | undefined) => {
    setParams({ ...params, action_type: value, page: 1 })
  }

  const handleDateRangeChange = (dates: [Dayjs | null, Dayjs | null] | null) => {
    setDateRange(dates)
    if (dates && dates[0] && dates[1]) {
      setParams({
        ...params,
        start_date: dates[0].startOf('day').toISOString(),
        end_date: dates[1].endOf('day').toISOString(),
        page: 1,
      })
    } else {
      setParams({
        ...params,
        start_date: undefined,
        end_date: undefined,
        page: 1,
      })
    }
  }

  const handleReset = () => {
    setDateRange(null)
    setParams({
      page: 1,
      page_size: 10,
      action_type: undefined,
      start_date: undefined,
      end_date: undefined,
    })
  }

  const renderChanges = (changes: Record<string, unknown> | null, actionType: AuditActionType) => {
    if (!changes) return '-'
    
    if (actionType === 'create') {
      return (
        <Space direction="vertical" size={0}>
          {Object.entries(changes).slice(0, 3).map(([key, value]) => (
            <Text key={key} type="secondary" style={{ fontSize: 12 }}>
              {key}: {String(value)}
            </Text>
          ))}
          {Object.keys(changes).length > 3 && (
            <Text type="secondary" style={{ fontSize: 12 }}>...</Text>
          )}
        </Space>
      )
    }
    
    if (actionType === 'update') {
      return (
        <Space direction="vertical" size={0}>
          {Object.entries(changes).slice(0, 3).map(([key, value]) => {
            const changeEntry = value as { old: unknown; new: unknown }
            return (
              <Text key={key} type="secondary" style={{ fontSize: 12 }}>
                {key}: <Text delete>{String(changeEntry.old)}</Text> → <Text type="success">{String(changeEntry.new)}</Text>
              </Text>
            )
          })}
          {Object.keys(changes).length > 3 && (
            <Text type="secondary" style={{ fontSize: 12 }}>...</Text>
          )}
        </Space>
      )
    }
    
    if (actionType === 'batch_update_status') {
      const count = Object.keys(changes).length
      return <Text type="secondary" style={{ fontSize: 12 }}>共 {count} 人状态变更</Text>
    }
    
    if (actionType === 'batch_delete') {
      const count = Object.keys(changes).length
      return <Text type="secondary" style={{ fontSize: 12 }}>共 {count} 人被删除</Text>
    }
    
    if (actionType === 'csv_import') {
      const csvChanges = changes as { imported_count: number }
      return (
        <Text type="secondary" style={{ fontSize: 12 }}>
          成功导入 {csvChanges.imported_count} 人
        </Text>
      )
    }
    
    if (actionType === 'delete') {
      return '-'
    }
    
    return '-'
  }

  const columns: ColumnsType<AuditLog> = [
    {
      title: '操作时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (dateStr: string) => dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作类型',
      dataIndex: 'action_type',
      key: 'action_type',
      width: 120,
      render: (type: AuditActionType) => {
        const info = actionTypeLabels[type]
        return <Tag color={info.color}>{info.text}</Tag>
      },
    },
    {
      title: '操作人',
      dataIndex: 'operator_name',
      key: 'operator_name',
      width: 120,
    },
    {
      title: '操作详情',
      dataIndex: 'details',
      key: 'details',
      width: 250,
      ellipsis: true,
    },
    {
      title: '变更内容',
      key: 'changes',
      width: 250,
      render: (_, record) => renderChanges(record.changes, record.action_type),
    },
    {
      title: '关联员工ID',
      dataIndex: 'target_ids',
      key: 'target_ids',
      width: 150,
      render: (ids: number[] | null) => {
        if (!ids || ids.length === 0) return '-'
        if (ids.length <= 5) {
          return (
            <Space size={[4, 4]} wrap>
              {ids.map(id => (
                <Tag key={id}>{id}</Tag>
              ))}
            </Space>
          )
        }
        return (
          <Space size={[4, 4]} wrap>
            {ids.slice(0, 5).map(id => (
              <Tag key={id}>{id}</Tag>
            ))}
            <Tag>...共{ids.length}人</Tag>
          </Space>
        )
      },
    },
  ]

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="操作类型筛选"
              allowClear
              style={{ width: '100%' }}
              value={params.action_type}
              onChange={handleActionTypeChange}
            >
              {Object.entries(actionTypeLabels).map(([value, info]) => (
                <Option key={value} value={value as AuditActionType}>
                  {info.text}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              style={{ width: '100%' }}
              value={dateRange}
              onChange={handleDateRangeChange}
              showTime
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button onClick={handleReset}>重置筛选</Button>
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
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          onChange={handleTableChange}
        />
      </Card>
    </div>
  )
}

export default AuditLogList
