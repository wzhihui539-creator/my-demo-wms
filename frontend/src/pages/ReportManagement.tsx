import React from 'react';
import { Card, Row, Col, Statistic, Table, DatePicker, Select, Button, message } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { api } from '../utils/api';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Option } = Select;

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function ReportManagement() {
  const [dateRange, setDateRange] = React.useState<any>([dayjs().subtract(30, 'days'), dayjs()]);
  const [warehouseId, setWarehouseId] = React.useState('');

  const { data: dashboardData } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/reports/dashboard').then(res => res.data),
  });

  const { data: inboundSummary } = useQuery({
    queryKey: ['inbound-summary'],
    queryFn: () => api.get('/reports/inbound/summary').then(res => res.data),
  });

  const { data: outboundSummary } = useQuery({
    queryKey: ['outbound-summary'],
    queryFn: () => api.get('/reports/outbound/summary').then(res => res.data),
  });

  const { data: inventoryByCategory } = useQuery({
    queryKey: ['inventory-by-category'],
    queryFn: () => api.get('/reports/inventory/by-category').then(res => res.data),
  });

  const { data: alertSummary } = useQuery({
    queryKey: ['alert-summary'],
    queryFn: () => api.get('/reports/alert/summary').then(res => res.data),
  });

  const handleExport = () => {
    message.info('导出功能开发中...');
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2>报表统计</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
          />
          <Select
            placeholder="选择仓库"
            value={warehouseId}
            onChange={setWarehouseId}
            style={{ width: 150 }}
          >
            <Option value="">全部仓库</Option>
          </Select>
          <Button type="primary" onClick={handleExport}>导出报表</Button>
        </div>
      </div>

      {/* 概览统计 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card>
            <Statistic title="总库存" value={dashboardData?.inventory?.total_quantity || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="SKU种类" value={dashboardData?.inventory?.sku_count || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="入库单数" value={inboundSummary?.order_count || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="入库数量" value={inboundSummary?.total_quantity || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="出库单数" value={outboundSummary?.order_count || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="出库数量" value={outboundSummary?.total_quantity || 0} />
          </Card>
        </Col>
      </Row>

      {/* 库存分类统计 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="库存分类分布">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={inventoryByCategory}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ category, percent }) => `${category}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="total_quantity"
                  nameKey="category"
                >
                  {inventoryByCategory?.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="预警统计">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={alertSummary?.type_stats || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8884d8" name="预警数量" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* 入库状态统计 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="入库状态分布">
            <Table
              dataSource={inboundSummary?.status_stats || []}
              columns={[
                { title: '状态', dataIndex: 'status', key: 'status' },
                { title: '单数', dataIndex: 'count', key: 'count' },
                { title: '数量', dataIndex: 'quantity', key: 'quantity' },
              ]}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="出库状态分布">
            <Table
              dataSource={outboundSummary?.status_stats || []}
              columns={[
                { title: '状态', dataIndex: 'status', key: 'status' },
                { title: '单数', dataIndex: 'count', key: 'count' },
                { title: '数量', dataIndex: 'quantity', key: 'quantity' },
              ]}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
