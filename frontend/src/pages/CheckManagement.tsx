import React, { useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, InputNumber, message, Space, Tag, Card, Row, Col, Statistic } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PlusOutlined, PlayCircleOutlined, CheckCircleOutlined, SearchOutlined } from '@ant-design/icons';
import { api } from '../utils/api';

const { Option } = Select;

export default function CheckManagement() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: orders, isLoading } = useQuery({
    queryKey: ['check-orders'],
    queryFn: async () => {
      try {
        const res = await api.get('/check/orders');
        if (Array.isArray(res.data)) return res.data;
        if (res.data && Array.isArray(res.data.items)) return res.data.items;
        return [];
      } catch (err) {
        console.error('获取盘点单失败:', err);
        return [];
      }
    },
    initialData: [],
  });

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/check/orders', data),
    onSuccess: () => {
      message.success('创建成功');
      setIsModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['check-orders'] });
    },
  });

  const startMutation = useMutation({
    mutationFn: (id) => api.post(`/check/orders/${id}/start`),
    onSuccess: () => {
      message.success('盘点开始');
      queryClient.invalidateQueries({ queryKey: ['check-orders'] });
    },
  });

  const completeMutation = useMutation({
    mutationFn: (id) => api.post(`/check/orders/${id}/complete`),
    onSuccess: () => {
      message.success('盘点完成');
      queryClient.invalidateQueries({ queryKey: ['check-orders'] });
    },
  });

  const statusColors = {
    pending: 'default',
    counting: 'processing',
    completed: 'success',
    cancelled: 'error',
  };

  const statusLabels = {
    pending: '待盘点',
    counting: '盘点中',
    completed: '已完成',
    cancelled: '已取消',
  };

  const columns = [
    { title: '盘点单号', dataIndex: 'order_no', key: 'order_no' },
    { title: '类型', dataIndex: 'check_type', key: 'check_type', render: (type) => type === 'full' ? '全盘' : type === 'partial' ? '抽盘' : '循环盘点' },
    { title: '仓库', dataIndex: 'warehouse_id', key: 'warehouse_id' },
    { title: '盘点项数', dataIndex: 'total_items', key: 'total_items' },
    { title: '匹配项', dataIndex: 'matched_items', key: 'matched_items' },
    { title: '差异项', dataIndex: 'diff_items', key: 'diff_items', render: (diff) => diff > 0 ? <Tag color="red">{diff}</Tag> : diff },
    { title: '状态', dataIndex: 'status', key: 'status', render: (status) => <Tag color={statusColors[status]}>{statusLabels[status]}</Tag> },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button icon={<SearchOutlined />} size="small" onClick={() => handleView(record)}>查看</Button>
          {record.status === 'pending' && (
            <Button icon={<PlayCircleOutlined />} size="small" type="primary" onClick={() => startMutation.mutate(record.id)}>开始</Button>
          )}
          {record.status === 'counting' && (
            <Button icon={<CheckCircleOutlined />} size="small" type="primary" onClick={() => completeMutation.mutate(record.id)}>完成</Button>
          )}
        </Space>
      ),
    },
  ];

  const handleView = (record) => {
    setEditingRecord(record);
    setIsModalOpen(true);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2>盘点管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingRecord(null); form.resetFields(); setIsModalOpen(true); }}>
          创建盘点单
        </Button>
      </div>

      <Table columns={columns} dataSource={orders} loading={isLoading} rowKey="id" />

      <Modal
        title={editingRecord ? '盘点单详情' : '创建盘点单'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={editingRecord ? [
          <Button key="close" onClick={() => setIsModalOpen(false)}>关闭</Button>,
        ] : [
          <Button key="cancel" onClick={() => setIsModalOpen(false)}>取消</Button>,
          <Button key="submit" type="primary" onClick={() => form.submit()} loading={createMutation.isPending}>确定</Button>,
        ]}
        width={800}
      >
        {editingRecord ? (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}><Card><Statistic title="盘点项数" value={editingRecord.total_items} /></Card></Col>
              <Col span={8}><Card><Statistic title="匹配项" value={editingRecord.matched_items} /></Card></Col>
              <Col span={8}><Card><Statistic title="差异项" value={editingRecord.diff_items} /></Card></Col>
            </Row>
            <Table
              dataSource={editingRecord.items}
              columns={[
                { title: '商品', dataIndex: 'sku_name', key: 'sku_name' },
                { title: '库位', dataIndex: 'location_code', key: 'location_code' },
                { title: '账面数量', dataIndex: 'book_qty', key: 'book_qty' },
                { title: '实际数量', dataIndex: 'actual_qty', key: 'actual_qty' },
                { title: '差异', dataIndex: 'diff_qty', key: 'diff_qty', render: (diff) => diff !== 0 ? <Tag color={diff > 0 ? 'green' : 'red'}>{diff > 0 ? '+' : ''}{diff}</Tag> : '-' },
                { title: '状态', dataIndex: 'status', key: 'status' },
              ]}
              rowKey="id"
              size="small"
            />
          </div>
        ) : (
          <Form form={form} layout="vertical" onFinish={(values) => createMutation.mutate(values)}>
            <Form.Item name="check_type" label="盘点类型" rules={[{ required: true }]}>
              <Select>
                <Option value="full">全盘</Option>
                <Option value="partial">抽盘</Option>
                <Option value="cycle">循环盘点</Option>
              </Select>
            </Form.Item>
            <Form.Item name="warehouse_id" label="仓库" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="remark" label="备注">
              <Input.TextArea />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  );
}
