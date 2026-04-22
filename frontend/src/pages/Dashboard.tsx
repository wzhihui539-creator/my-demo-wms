import React from 'react';
import { Card, Row, Col, Statistic, Table, Badge } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { ArrowUpOutlined, ArrowDownOutlined, ExclamationCircleOutlined, InboxOutlined } from '@ant-design/icons';
import { api } from '../utils/api';

export default function Dashboard() {
  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/reports/dashboard').then(res => res.data),
  });

  const pendingTasks = dashboardData?.pending_tasks || {};
  const inventory = dashboardData?.inventory || {};
  const inboundToday = dashboardData?.inbound_today || {};
  const outboundToday = dashboardData?.outbound_today || {};

  const taskColumns = [
    { title: '任务类型', dataIndex: 'type', key: 'type' },
    { title: '待处理数量', dataIndex: 'count', key: 'count', render: (count: number) => <Badge count={count} showZero color={count > 0 ? '#f5222d' : '#52c41a'} /> },
  ];

  const taskData = [
    { key: '1', type: '待处理预警', count: pendingTasks.alerts || 0 },
    { key: '2', type: '待处理入库单', count: pendingTasks.inbound_orders || 0 },
    { key: '3', type: '待处理出库单', count: pendingTasks.outbound_orders || 0 },
  ];

  return (
    <div>
      <h2>仪表盘</h2>
      
      {/* 库存概览 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card loading={isLoading}>
            <Statistic
              title="总库存数量"
              value={inventory.total_quantity || 0}
              prefix={<InboxOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={isLoading}>
            <Statistic
              title="SKU种类"
              value={inventory.sku_count || 0}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={isLoading}>
            <Statistic
              title="今日入库"
              value={inboundToday.total_quantity || 0}
              prefix={<ArrowUpOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={isLoading}>
            <Statistic
              title="今日出库"
              value={outboundToday.total_quantity || 0}
              prefix={<ArrowDownOutlined style={{ color: '#f5222d' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 待处理任务 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card title="待处理任务" extra={<ExclamationCircleOutlined style={{ color: '#f5222d' }} />}>
            <Table columns={taskColumns} dataSource={taskData} pagination={false} size="small" />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="库存利用率">
            <Statistic
              title="库位利用率"
              value={inventory.location_utilization || 0}
              suffix="%"
              precision={2}
            />
            <div style={{ marginTop: 16 }}>
              <p>已使用库位: {inventory.location_count - inventory.empty_location_count || 0}</p>
              <p>空库位: {inventory.empty_location_count || 0}</p>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
