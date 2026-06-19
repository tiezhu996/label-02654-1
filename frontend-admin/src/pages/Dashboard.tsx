import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Spin } from 'antd'
import {
  TeamOutlined,
  UserAddOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import { employeeApi, Statistics } from '../api/employee'

const Dashboard = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Statistics | null>(null)

  useEffect(() => {
    loadStatistics()
  }, [])

  const loadStatistics = async () => {
    try {
      const data = await employeeApi.getStatistics()
      setStats(data)
    } catch {
      // Error handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  // Department distribution pie chart
  const getDeptChartOption = () => ({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        data: stats?.department_distribution.map((item) => ({
          name: item.department,
          value: item.count,
        })) || [],
      },
    ],
  })

  // Gender distribution pie chart
  const getGenderChartOption = () => ({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
    },
    color: ['#1677ff', '#ff85c0'],
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        data: [
          { name: '男', value: stats?.gender_distribution.male || 0 },
          { name: '女', value: stats?.gender_distribution.female || 0 },
        ],
      },
    ],
  })

  // Status distribution pie chart
  const getStatusChartOption = () => ({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
    },
    color: ['#52c41a', '#ff4d4f'],
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        data: [
          { name: '在职', value: stats?.active || 0 },
          { name: '离职', value: stats?.inactive || 0 },
        ],
      },
    ],
  })

  // Hire trend line chart
  const getTrendChartOption = () => ({
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: stats?.hire_trend.map((item) => item.month) || [],
      axisLabel: {
        rotate: 45,
      },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
    },
    series: [
      {
        type: 'line',
        data: stats?.hire_trend.map((item) => item.count) || [],
        smooth: true,
        areaStyle: {
          opacity: 0.3,
        },
        itemStyle: {
          color: '#1677ff',
        },
      },
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true,
    },
  })

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      {/* Statistics Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="员工总数"
              value={stats?.total || 0}
              prefix={<TeamOutlined style={{ color: '#1677ff' }} />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="在职员工"
              value={stats?.active || 0}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="离职员工"
              value={stats?.inactive || 0}
              prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="本月入职"
              value={stats?.this_month_hires || 0}
              prefix={<UserAddOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="部门人数分布">
            <ReactECharts
              option={getDeptChartOption()}
              style={{ height: 300 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="入职趋势（近12个月）">
            <ReactECharts
              option={getTrendChartOption()}
              style={{ height: 300 }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="性别比例">
            <ReactECharts
              option={getGenderChartOption()}
              style={{ height: 300 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="在职/离职状态">
            <ReactECharts
              option={getStatusChartOption()}
              style={{ height: 300 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
