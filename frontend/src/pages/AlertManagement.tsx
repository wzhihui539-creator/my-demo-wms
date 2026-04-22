import React, { useState, useCallback } from 'react';
import { Table, Button, Modal, Form, Input, Select, InputNumber, Switch, message, Space, Tag, Card, Row, Col, Statistic, Badge } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PlusOutlined, BellOutlined, CheckCircleOutlined, EyeOutlined } from '@ant-design/icons';
import { api } from '../utils/api';

const { Option } = Select;

export default function AlertManagement() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isRecordModalOpen, setIsRecordModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: rules, isLoading: rulesLoading } = useQuery({
    queryKey: ['alert-rules'],
    queryFn: async () => {
      try {
        const res = await api.get('/alerts/rules');
        return Array.isArray(res.data) ? res.data : [];
      } catch (err) {
        return [];
      }
    },
    initialData: [],
  });

  const { data: records, isLoading: recordsLoading } = useQuery({
    queryKey: ['alert-records'],
    queryFn: async () => {
      try {
        const res = await api.get('/alerts/records');
        return Array.isArray(res.data) ? res.data : [];
      } catch (err) {
        return [];
      }
    },
    initialData: [],
  });

  const { data: stats } = useQuery({
    queryKey: ['alert-stats'],
    queryFn: async () => {
      try {
        const res = await api.get('/alerts/stats');
        return res.data || {};
      } catch (err) {
        return {};
      }
    },
    initialData: {},
  });

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/alerts/rules', data),
    onSuccess: () => {
      message.success('创建成功');
      setIsModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  const checkMutation = useMutation({
    mutationFn: () => api.post('/alerts/check'),
    onSuccess: (res) => {
      message.success(`检查完成，发现 ${res.data?.length || 0} 条预警`);
      queryClient.invalidateQueries({ queryKey: ['alert-records'] });
      queryClient.invalidateQueries({ queryKey: ['alert-stats'] });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (id) => api.post(`/alerts/records/${id}/resolve`, {}),
    onSuccess: () => {
      message.success('已处理');
      setIsRecordModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['alert-records'] });
      queryClient.invalidateQueries({ queryKey: ['alert-stats'] });
    },
  });

  const typeLabels: Record<string, string> = {
    low_stock: '低库存',
    high_stock: '高库存',
    expired: '临期',
    stagnant: '呆滞',
  };

  const levelColors: Record<string, any> = {
    warning: 'orange',
    critical: 'red',
  };

  const statusColors: Record<string, any> = {
    unread: 'red',
    read: 'blue',
    resolved: 'green',
  };

  const ruleColumns = [
    { title: '预警类型', dataIndex: 'alert_type', key: 'alert_type', render: (type: string) => typeLabels[type] },
    { title: '商品', dataIndex: 'sku_id', key: 'sku_id' },
    { title: '仓库', dataIndex: 'warehouse_id', key: 'warehouse_id' },
    { title: '最小阈值', dataIndex: 'threshold_min', key: 'threshold_min' },
    { title: '最大阈值', dataIndex: 'threshold_max', key: 'threshold_max' },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', render: (active: boolean) => <Switch checked={active} disabled /> },
    { title: '触发次数', dataIndex: 'trigger_count', key: 'trigger_count' },
  ];

  const recordColumns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '类型', dataIndex: 'alert_type', key: 'alert_type', render: (type: string) => <Tag>{typeLabels[type]}</Tag> },
    { title: '级别', dataIndex: 'alert_level', key: 'alert_level', render: (level: string) => <Tag color={levelColors[level]}>{level}</Tag> },
    { title: '当前数量', dataIndex: 'current_qty', key: 'current_qty' },
    { title: '阈值', dataIndex: 'threshold_value', key: 'threshold_value' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (status: string) => <Badge status={statusColors[status]} text={status} /> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button icon={<EyeOutlined />} size="small" onClick={() => { setSelectedRecord(record); setIsRecordModalOpen(true); }}>查看</Button>
          {record.status !== 'resolved' && (
            <Button icon={<CheckCircleOutlined />} size="small" type="primary" onClick={() => resolveMutation.mutate(record.id)}>处理</Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2>预警管理</h2>
        <Space>
          <Button icon={<BellOutlined />} onClick={() => checkMutation.mutate()} loading={checkMutation.isPending}>检查预警</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingRecord(null); form.resetFields(); setIsModalOpen(true); }}>
            创建规则
          </Button>
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}><Card><Statistic title="总预警" value={stats?.total_alerts || 0} /></Card></Col>
        <Col span={4}><Card><Statistic title="未读" value={stats?.unread_count || 0} valueStyle={{ color: '#cf1322' }} /></Card></Col>
        <Col span={4}><Card><Statistic title="警告" value={stats?.warning_count || 0} valueStyle={{ color: '#faad14' }} /></Card></Col>
        <Col span={4}><Card><Statistic title="严重" value={stats?.critical_count || 0} valueStyle={{ color: '#cf1322' }} /></Card></Col>
        <Col span={4}><Card><Statistic title="低库存" value={stats?.low_stock_count || 0} /></Card></Col>
        <Col span={4}><Card><Statistic title="高库存" value={stats?.high_stock_count || 0} /></Card></Col>
      </Row>

      {/* 预警记录 */}
      <Card title="预警记录" style={{ marginBottom: 24 }}>
        <Table columns={recordColumns} dataSource={records || []} loading={recordsLoading} rowKey="id" />
      </Card>

      {/* 预警规则 */}
      <Card title="预警规则">
        <Table columns={ruleColumns} dataSource={rules || []} loading={rulesLoading} rowKey="id" />
      </Card>

      {/* 创建规则模态框 */}
      <Modal
        title="创建预警规则"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={[
          <Button key="cancel" onClick={() => setIsModalOpen(false)}>取消</Button>,
          <Button key="submit" type="primary" onClick={() => form.submit()} loading={createMutation.isPending}>确定</Button>,
        ]}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={(values) => createMutation.mutate(values)}>
          <Form.Item name="alert_type" label="预警类型" rules={[{ required: true }]}>
            <Select>
              <Option value="low_stock">低库存</Option>
              <Option value="high_stock">高库存</Option>
              <Option value="expired">临期</Option>
              <Option value="stagnant">呆滞</Option>
            </Select>
          </Form.Item>
          <Form.Item name="sku_id" label="商品ID">
            <Input placeholder="留空则监控所有商品" />
          </Form.Item>
          <Form.Item name="warehouse_id" label="仓库ID">
            <Input placeholder="留空则监控所有仓库" />
          </Form.Item>
          <Form.Item name="threshold_min" label="最小阈值">
            <InputNumber style={{ width: '100%' }} placeholder="低库存预警必填" />
          </Form.Item>
          <Form.Item name="threshold_max" label="最大阈值">
            <InputNumber style={{ width: '100%' }} placeholder="高库存预警必填" />
          </Form.Item>
          <Form.Item name="notify_emails" label="通知邮箱">
            <Input placeholder="多个邮箱用逗号分隔" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 预警详情模态框 */}
      <Modal
        title="预警详情"
        open={isRecordModalOpen}
        onCancel={() => setIsRecordModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setIsRecordModalOpen(false)}>关闭</Button>,
          selectedRecord?.status !== 'resolved' && (
            <Button key="resolve" type="primary" onClick={() => resolveMutation.mutate(selectedRecord.id)} loading={resolveMutation.isPending}>标记已处理</Button>
          ),
        ]}
      >
        {selectedRecord && (
          <div>
            <p><strong>标题:</strong> {selectedRecord.title}</p>
            <p><strong>内容:</strong> {selectedRecord.content}</p>
            <p><strong>类型:</strong> {typeLabels[selectedRecord.alert_type]}</p>
            <p><strong>级别:</strong> <Tag color={levelColors[selectedRecord.alert_level]}>{selectedRecord.alert_level}</Tag></p>
            <p><strong>当前数量:</strong> {selectedRecord.current_qty}</p>
            <p><strong>阈值:</strong> {selectedRecord.threshold_value}</p>
            <p><strong>状态:</strong> <Badge status={statusColors[selectedRecord.status]} text={selectedRecord.status} /></p>
            <p><strong>创建时间:</strong> {selectedRecord.created_at}</p>
          </div>
        )}
      </Modal>
    </div>
  );
}
