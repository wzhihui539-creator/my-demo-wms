import React, { useState, useCallback, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, InputNumber, Select, message, Space, Tag, Card, Row, Col, Statistic as AntStatistic } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import { api } from '../utils/api';

interface InventoryItem {
  id: string;
  sku_id: string;
  sku_code?: string;
  sku_name?: string;
  location_id: string;
  location_code?: string;
  quantity: number;
  available_qty: number;
  locked_qty: number;
  status: string;
}

export default function InventoryManagement() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<InventoryItem | null>(null);
  const [searchSku, setSearchSku] = useState('');
  const [form] = Form.useForm();

  const queryClient = useQueryClient();

  const { data: inventories, isLoading, error, refetch } = useQuery({
    queryKey: ['inventories', searchSku],
    queryFn: async () => {
      try {
        const url = searchSku ? `/inventory/sku/${searchSku}` : '/inventory';
        const res = await api.get(url);
        // 确保返回数组
        if (Array.isArray(res.data)) {
          return res.data;
        }
        if (res.data && Array.isArray(res.data.items)) {
          return res.data.items;
        }
        return [];
      } catch (err) {
        console.error('获取库存失败:', err);
        return [];
      }
    },
    initialData: [],
  });

  const { data: summary } = useQuery({
    queryKey: ['inventory-summary'],
    queryFn: async () => {
      try {
        const res = await api.get('/reports/inventory/summary');
        return res.data || {};
      } catch (err) {
        console.error('获取库存概览失败:', err);
        return {};
      }
    },
    initialData: {},
  });

  const adjustMutation = useMutation({
    mutationFn: ({ inventoryId, data }: { inventoryId: string; data: any }) =>
      api.put(`/inventory/${inventoryId}/adjust`, data),
    onSuccess: () => {
      message.success('库存调整成功');
      setIsModalOpen(false);
      setEditingRecord(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['inventories'] });
      queryClient.invalidateQueries({ queryKey: ['inventory-summary'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '库存调整失败');
    },
  });

  // 监听入库/出库操作，自动刷新库存
  useEffect(() => {
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['inventories'] });
      queryClient.invalidateQueries({ queryKey: ['inventory-summary'] });
    }, 30000); // 每30秒自动刷新
    return () => clearInterval(interval);
  }, [queryClient]);

  const statusColors: Record<string, string> = {
    normal: 'green',
    empty: 'default',
    locked: 'orange',
    damaged: 'red',
  };

  const columns = [
    {
      title: '商品',
      dataIndex: 'sku_id',
      key: 'sku_id',
      render: (_: string, record: InventoryItem) => record.sku_name || record.sku_code || record.sku_id,
    },
    {
      title: '库位',
      dataIndex: 'location_id',
      key: 'location_id',
      render: (_: string, record: InventoryItem) => record.location_code || record.location_id,
    },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '可用数量', dataIndex: 'available_qty', key: 'available_qty' },
    { title: '锁定数量', dataIndex: 'locked_qty', key: 'locked_qty' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (status: string) => <Tag color={statusColors[status]}>{status}</Tag> },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: InventoryItem) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record)}>调整</Button>
          <Button icon={<ReloadOutlined />} size="small" onClick={() => refetch()}>刷新</Button>
        </Space>
      ),
    },
  ];

  const handleEdit = useCallback((record: InventoryItem) => {
    setEditingRecord(record);
    form.setFieldsValue(record);
    setIsModalOpen(true);
  }, [form]);

  const handleAdjustSubmit = useCallback((values: any) => {
    if (!editingRecord) return;
    adjustMutation.mutate({ inventoryId: editingRecord.id, data: values });
  }, [adjustMutation, editingRecord]);

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <div style={{ color: 'red', marginBottom: 16 }}>加载失败: {error.message}</div>
        <Button type="primary" onClick={() => window.location.reload()}>刷新页面</Button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2>库存管理</h2>
        <Space>
          <Input
            placeholder="搜索商品ID"
            value={searchSku}
            onChange={(e) => setSearchSku(e.target.value)}
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
          />
          <Button onClick={() => setSearchSku('')}>重置</Button>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>刷新</Button>
        </Space>
      </div>

      {/* 库存概览 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <AntStatistic title="总库存数量" value={summary?.total_quantity || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <AntStatistic title="SKU种类" value={summary?.sku_count || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <AntStatistic title="库位数量" value={summary?.location_count || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <AntStatistic title="空库位" value={summary?.empty_location_count || 0} />
          </Card>
        </Col>
      </Row>

      <Table columns={columns} dataSource={inventories || []} loading={isLoading} rowKey="id" />

      <Modal
        title="调整库存"
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false);
          setEditingRecord(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
        destroyOnClose={true}
      >
        <Form form={form} layout="vertical" onFinish={handleAdjustSubmit}>
          <Form.Item label="商品">
            <Input value={editingRecord?.sku_name || editingRecord?.sku_code || editingRecord?.sku_id} disabled />
          </Form.Item>
          <Form.Item label="库位">
            <Input value={editingRecord?.location_code || editingRecord?.location_id} disabled />
          </Form.Item>
          <Form.Item name="quantity" label="数量">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="available_qty" label="可用数量">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="locked_qty" label="锁定数量">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select>
              <Select.Option value="normal">normal</Select.Option>
              <Select.Option value="empty">empty</Select.Option>
              <Select.Option value="locked">locked</Select.Option>
              <Select.Option value="damaged">damaged</Select.Option>
            </Select>
          </Form.Item>
          <Space style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button onClick={() => setIsModalOpen(false)}>取消</Button>
            <Button type="primary" htmlType="submit" loading={adjustMutation.isPending}>保存</Button>
          </Space>
        </Form>
      </Modal>
    </div>
  );
}
