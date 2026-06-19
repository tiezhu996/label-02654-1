import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Form,
  Input,
  Select,
  DatePicker,
  InputNumber,
  Button,
  Card,
  message,
  Spin,
  Space,
  AutoComplete,
} from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  employeeApi,
  CreateEmployeeParams,
  UpdateEmployeeParams,
} from '../api/employee'

const { Option } = Select

const EmployeeForm = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [departments, setDepartments] = useState<string[]>([])

  const isEdit = !!id

  useEffect(() => {
    loadDepartments()
    if (isEdit) {
      loadEmployee()
    }
  }, [id])

  const loadDepartments = async () => {
    try {
      const response = await employeeApi.getDepartments()
      setDepartments(response.departments)
    } catch {
      // Error handled by interceptor
    }
  }

  const loadEmployee = async () => {
    if (!id) return
    setLoading(true)
    try {
      const employee = await employeeApi.getById(parseInt(id))
      form.setFieldsValue({
        ...employee,
        hire_date: dayjs(employee.hire_date),
      })
    } catch {
      // Error handled by interceptor
      navigate('/employees')
    } finally {
      setLoading(false)
    }
  }

  const onFinish = async (values: CreateEmployeeParams & { hire_date: dayjs.Dayjs }) => {
    setSubmitting(true)
    try {
      const data = {
        ...values,
        hire_date: values.hire_date.format('YYYY-MM-DD'),
      }

      if (isEdit && id) {
        await employeeApi.update(parseInt(id), data as UpdateEmployeeParams)
        message.success('更新成功')
      } else {
        await employeeApi.create(data as CreateEmployeeParams)
        message.success('创建成功')
      }
      navigate('/employees')
    } catch {
      // Error handled by interceptor
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
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
            {isEdit ? '编辑员工' : '添加员工'}
          </Space>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          style={{ maxWidth: 600 }}
          initialValues={{
            gender: 'male',
            status: 'active',
          }}
        >
          <Form.Item
            label="姓名"
            name="name"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>

          <Form.Item
            label="性别"
            name="gender"
            rules={[{ required: true, message: '请选择性别' }]}
          >
            <Select placeholder="请选择性别">
              <Option value="male">男</Option>
              <Option value="female">女</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="年龄"
            name="age"
            rules={[
              { required: true, message: '请输入年龄' },
              { type: 'number', min: 18, max: 100, message: '年龄范围: 18-100' },
            ]}
          >
            <InputNumber
              placeholder="请输入年龄"
              style={{ width: '100%' }}
              min={18}
              max={100}
            />
          </Form.Item>

          <Form.Item
            label="部门"
            name="department"
            rules={[{ required: true, message: '请输入部门' }]}
          >
            <AutoComplete
              placeholder="请输入或选择部门"
              options={departments.map((dept) => ({ value: dept, label: dept }))}
              filterOption={(inputValue, option) =>
                option?.value.toLowerCase().includes(inputValue.toLowerCase()) ?? false
              }
              allowClear
            />
          </Form.Item>

          <Form.Item
            label="职位"
            name="position"
            rules={[{ required: true, message: '请输入职位' }]}
          >
            <Input placeholder="请输入职位" />
          </Form.Item>

          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>

          <Form.Item label="电话" name="phone">
            <Input placeholder="请输入电话" />
          </Form.Item>

          <Form.Item
            label="入职日期"
            name="hire_date"
            rules={[{ required: true, message: '请选择入职日期' }]}
          >
            <DatePicker style={{ width: '100%' }} placeholder="请选择入职日期" />
          </Form.Item>

          <Form.Item
            label="状态"
            name="status"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select placeholder="请选择状态">
              <Option value="active">在职</Option>
              <Option value="inactive">离职</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={submitting}>
                {isEdit ? '保存' : '创建'}
              </Button>
              <Button onClick={() => navigate('/employees')}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default EmployeeForm
