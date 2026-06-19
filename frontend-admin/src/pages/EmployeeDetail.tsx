import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Space, Spin } from 'antd'
import {
  ArrowLeftOutlined,
  EditOutlined,
  ManOutlined,
  WomanOutlined,
} from '@ant-design/icons'
import { employeeApi, Employee } from '../api/employee'
import { useAuthStore } from '../stores/authStore'

const EmployeeDetail = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const { isAdmin } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [employee, setEmployee] = useState<Employee | null>(null)

  useEffect(() => {
    loadEmployee()
  }, [id])

  const loadEmployee = async () => {
    if (!id) return
    setLoading(true)
    try {
      const data = await employeeApi.getById(parseInt(id))
      setEmployee(data)
    } catch {
      // Error handled by interceptor
      navigate('/employees')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!employee) {
    return null
  }

  return (
    <div>
      <Card
        title={
          <Space>
            <Button
              type="text"
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/employees')}
            />
            员工详情
          </Space>
        }
        extra={
          isAdmin && (
            <Button
              type="primary"
              icon={<EditOutlined />}
              onClick={() => navigate(`/employees/${id}/edit`)}
            >
              编辑
            </Button>
          )
        }
      >
        <Descriptions bordered column={{ xs: 1, sm: 2 }}>
          <Descriptions.Item label="工号">{employee.employee_id}</Descriptions.Item>
          <Descriptions.Item label="姓名">{employee.name}</Descriptions.Item>
          <Descriptions.Item label="性别">
            {employee.gender === 'male' ? (
              <span>
                <ManOutlined style={{ color: '#1677ff', marginRight: 4 }} />
                男
              </span>
            ) : (
              <span>
                <WomanOutlined style={{ color: '#ff85c0', marginRight: 4 }} />
                女
              </span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="年龄">{employee.age} 岁</Descriptions.Item>
          <Descriptions.Item label="部门">{employee.department}</Descriptions.Item>
          <Descriptions.Item label="职位">{employee.position}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{employee.email}</Descriptions.Item>
          <Descriptions.Item label="电话">{employee.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="入职日期">{employee.hire_date}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={employee.status === 'active' ? 'green' : 'red'}>
              {employee.status === 'active' ? '在职' : '离职'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(employee.created_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {employee.updated_at
              ? new Date(employee.updated_at).toLocaleString()
              : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )
}

export default EmployeeDetail
