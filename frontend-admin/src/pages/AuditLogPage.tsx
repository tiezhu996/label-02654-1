import { useEffect, useMemo, useState } from 'react'
import {
  Card,
  Table,
  Tag,
  Select,
  DatePicker,
  Row,
  Col,
  Space,
  Typography,
  Button,
} from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import {
  auditLogApi,
  AuditAction,
  AuditLog,
  AuditLogListParams,
} from '../api/auditLog'

const { RangePicker } = DatePicker
const { Text, Paragraph } = Typography

const ACTION_LABELS: Record<AuditAction, { label: string; color: string }> = {
  create: { label: '新增', color: 'blue' },
  update: { label: '修改', color: 'gold' },
  delete: { label: '删除', color: 'red' },
  bulk_update: { label: '批量修改', color: 'orange' },
  bulk_delete: { label: '批量删除', color: 'volcano' },
  import: { label: 'CSV 导入', color: 'geekblue' },
}

const AuditLogPage = () => {
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [total, setTotal] = useState(0)
  const [params, setParams] = useState<AuditLogListParams>({
    page: 1,
    page_size: 20,
    action: undefined,
    start_time: undefined,
    end_time: undefined,
  })
  const [range, setRange] = useState<[Dayjs | null, Dayjs | null] | null>(null)

  useEffect(() => {
    loadLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      page_size: pagination.pageSize || 20,
    })
  }

  const handleActionFilter = (value?: AuditAction) => {
    setParams({ ...params, action: value, page: 1 })
  }

  const handleRangeChange = (
    values: [Dayjs | null, Dayjs | null] | null
  ): void => {
    setRange(values)
    setParams({
      ...params,
      start_time: values?.[0] ? values[0].toISOString() : undefined,
      end_time: values?.[1] ? values[1].toISOString() : undefined,
      page: 1,
    })
  }

  const handleReset = () => {
    setRange(null)
    setParams({
      page: 1,
      page_size: params.page_size,
      action: undefined,
      start_time: undefined,
      end_time: undefined,
    })
  }

  const columns: ColumnsType<AuditLog> = useMemo(
    () => [
      {
        title: '时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 180,
        render: (value: string) =>
          dayjs(value).format('YYYY-MM-DD HH:mm:ss'),
      },
      {
        title: '操作类型',
        dataIndex: 'action',
        key: 'action',
        width: 120,
        render: (action: AuditAction) => {
          const conf = ACTION_LABELS[action]
          return <Tag color={conf?.color}>{conf?.label || action}</Tag>
        },
      },
      {
        title: '操作人',
        dataIndex: 'operator_name',
        key: 'operator_name',
        width: 140,
      },
      {
        title: '目标',
        key: 'target',
        width: 200,
        render: (_, record) => {
          if (!record.target_id && !record.target_name) {
            return <Text type="secondary">-</Text>
          }
          return (
            <span>
              {record.target_name || ''}
              {record.target_id && (
                <Text type="secondary"> (ID:{record.target_id})</Text>
              )}
            </span>
          )
        },
      },
      {
        title: '说明',
        dataIndex: 'summary',
        key: 'summary',
        ellipsis: true,
      },
      {
        title: '关键变更',
        dataIndex: 'changes',
        key: 'changes',
        width: 320,
        render: (changes: AuditLog['changes']) => {
          if (!changes) return <Text type="secondary">-</Text>
          return (
            <Paragraph
              style={{ marginBottom: 0 }}
              ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
            >
              <Text code style={{ whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(changes, null, 2)}
              </Text>
            </Paragraph>
          )
        },
      },
    ],
    []
  )

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="操作类型"
              allowClear
              style={{ width: '100%' }}
              value={params.action}
              onChange={handleActionFilter}
              options={(Object.keys(ACTION_LABELS) as AuditAction[]).map(
                (key) => ({
                  value: key,
                  label: ACTION_LABELS[key].label,
                })
              )}
            />
          </Col>
          <Col xs={24} sm={12} md={10}>
            <RangePicker
              showTime
              style={{ width: '100%' }}
              value={range}
              onChange={handleRangeChange}
            />
          </Col>
          <Col xs={24} sm={12} md={8} style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={handleReset}>重置筛选</Button>
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={loadLogs}
              >
                刷新
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
          scroll={{ x: 1200 }}
          pagination={{
            current: params.page,
            pageSize: params.page_size,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (count) => `共 ${count} 条记录`,
          }}
          onChange={handleTableChange}
        />
      </Card>
    </div>
  )
}

export default AuditLogPage
