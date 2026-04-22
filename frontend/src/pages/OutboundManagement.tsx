import React, { useState, useCallback } from 'react';
import { Table, Button, Modal, Form, Input, Select, InputNumber, message, Space, Tag, Popconfirm } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PlusOutlined, EditOutlined, EyeOutlined, PlayCircleOutlined, CheckCircleOutlined, CarOutlined } from '@ant-design/icons';
import { api } from '../utils/api';

const { Option } = Select;

interface OutboundItem {
  sku_id: string;
  expected_qty: number;
}

interface OutboundOrder {
  id: string;
  order_no: string;
  order_type: 'sales' | 'transfer';
  warehouse_id: string;
  total_qty: number;
  status: string;
  priority: string;
  remark?: string;
  items: OutboundItem[];
  created_at: string;
}

export default function OutboundManagement() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<OutboundOrder | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: warehouses } = useQuery({
    queryKey: ['warehouses'],
    queryFn: async () => {
      try {
        const res = await api.get('/warehouses');
        return Array.isArray(res.data) ? res.data : [];
      } catch (err) {
        return [];
      }
    },
    initialData: [],
  });

  const { data: skus } = useQuery({
    queryKey: ['skus'],
    queryFn: async () => {
      try {
        const res = await api.get('/skus');
        return Array.isArray(res.data) ? res.data : [];
      } catch (err) {
        return [];
      }
    },
    initialData: [],
  });

  const { data: locations } = useQuery({
    queryKey: ['locations'],
    queryFn: async () => {
      try {
        const res = await api.get('/locations');
        return Array.isArray(res.data) ? res.data : [];
      } catch (err) {
        return [];
      }
    },
    initialData: [],
  });

  const { data: orders, isLoading } = useQuery({
    queryKey: ['outbound-orders'],
    queryFn: async () => {
      try {
        const res = await api.get('/outbound/orders');
        if (Array.isArray(res.data)) return res.data;
        if (res.data && Array.isArray(res.data.items)) return res.data.items;
        return [];
      } catch (err) {
        console.error('获取出库单失败:', err);
        return [];
      }
    },
    initialData: [],
  });

  // 拣货操作
  const startPickMutation = useMutation({
    mutationFn: ({ orderId, data }: { orderId: string; data: any }) =>
      api.post(`/outbound/orders/${orderId}/start-pick`, data),
    onSuccess: () => {
      message.success('已开始拣货');
      queryClient.invalidateQueries({ queryKey: ['outbound-orders'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '开始拣货失败');
    },
  });

  const pickMutation = useMutation({
    mutationFn: ({ orderId, data }: { orderId: string; data: any }) =>
      api.post(`/outbound/orders/${orderId}/pick`, data),
    onSuccess: () => {
      message.success('拣货成功');
      queryClient.invalidateQueries({ queryKey: ['outbound-orders'] });
      queryClient.invalidateQueries({ queryKey: ['inventories'] });
      setIsActionModalOpen(false);
      setActionFormData(null);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '拣货失败');
    },
  });

  // 发货操作
  const shipMutation = useMutation({
    mutationFn: ({ orderId, data }: { orderId: string; data: any }) =>
      api.post(`/outbound/orders/${orderId}/ship`, data),
    onSuccess: () => {
      message.success('发货成功');
      queryClient.invalidateQueries({ queryKey: ['outbound-orders'] });
      setIsActionModalOpen(false);
      setActionFormData(null);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '发货失败');
    },
  });

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/outbound/orders', data),
    onSuccess: () => {
      message.success('创建成功');
      setIsModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['outbound-orders'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '创建失败');
    },
  });

  const [isActionModalOpen, setIsActionModalOpen] = useState(false);
  const [actionType, setActionType] = useState<'pick' | 'ship' | null>(null);
  const [actionRecord, setActionRecord] = useState<OutboundOrder | null>(null);
  const [actionFormData, setActionFormData] = useState<any>(null);

  const statusColors: Record<string, string> = {
    pending: 'default',
    picking: 'processing',
    picked: 'warning',
    shipped: 'warning',
    completed: 'success',
    cancelled: 'error',
  };

  const statusLabels: Record<string, string> = {
    pending: '待处理',
    picking: '拣货中',
    picked: '已拣货',
    shipped: '已发货',
    completed: '已完成',
    cancelled: '已取消',
  };

  const getNextAction = (record: OutboundOrder) => {
    switch (record.status) {
      case 'pending':
        return { type: 'start-pick' as const, label: '开始拣货', icon: <PlayCircleOutlined /> };
      case 'picking':
        return { type: 'pick' as const, label: '继续拣货', icon: <CheckCircleOutlined /> };
      case 'picked':
        return { type: 'ship' as const, label: '发货', icon: <CarOutlined /> };
      case 'shipped':
        return { type: 'ship' as const, label: '继续发货', icon: <CheckCircleOutlined /> };
      default:
        return null;
    }
  };

  const handleStartPick = (record: OutboundOrder) => {
    startPickMutation.mutate({ orderId: record.id, data: {} });
  };

  const handleAction = (record: OutboundOrder, type: 'pick' | 'ship') => {
    setActionRecord(record);
    setActionType(type);
    setActionFormData({});
    setIsActionModalOpen(true);
  };

  const handleActionSubmit = () => {
    if (!actionRecord || !actionFormData) return;

    if (actionType === 'pick') {
      pickMutation.mutate({ orderId: actionRecord.id, data: actionFormData });
    } else if (actionType === 'ship') {
      shipMutation.mutate({ orderId: actionRecord.id, data: actionFormData });
    }
  };

  const columns = [
    { title: '出库单号', dataIndex: 'order_no', key: 'order_no' },
    { title: '类型', dataIndex: 'order_type', key: 'order_type', render: (type: string) => type === 'sales' ? '销售出库' : '调拨出库' },
    { title: '仓库', dataIndex: 'warehouse_id', key: 'warehouse_id' },
    { title: '总数量', dataIndex: 'total_qty', key: 'total_qty' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (status: string) => <Tag color={statusColors[status]}>{statusLabels[status]}</Tag> },
    { title: '优先级', dataIndex: 'priority', key: 'priority', render: (priority: string) => priority === 'high' ? <Tag color="red">高</Tag> : <Tag>普通</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: OutboundOrder) => {
        const nextAction = getNextAction(record);
        return (
          <Space>
            <Button icon={<EyeOutlined />} size="small" onClick={() => handleView(record)}>查看</Button>
            {record.status === 'pending' && (
              <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)}>编辑</Button>
            )}
            {nextAction && (
              nextAction.type === 'start-pick' ? (
                <Popconfirm
                  title="确认开始拣货？"
                  description="开始后订单状态会变为“拣货中”"
                  onConfirm={() => handleStartPick(record)}
                  okText="确认"
                  cancelText="取消"
                >
                  <Button
                    type="primary"
                    size="small"
                    icon={nextAction.icon}
                    loading={startPickMutation.isPending}
                  >
                    {nextAction.label}
                  </Button>
                </Popconfirm>
              ) : (
                <Button
                  type="primary"
                  size="small"
                  icon={nextAction.icon}
                  onClick={() => handleAction(record, nextAction.type)}
                >
                  {nextAction.label}
                </Button>
              )
            )}
          </Space>
        );
      },
    },
  ];

  const handleView = useCallback((record: OutboundOrder) => {
    setEditingRecord(record);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((record: OutboundOrder) => {
    setEditingRecord(record);
    form.setFieldsValue(record);
    setIsModalOpen(true);
  }, [form]);

  const handleSubmit = useCallback((values: any) => {
    const payload = {
      ...values,
      items: values.items || [],
    };
    createMutation.mutate(payload);
  }, [createMutation]);

  const openCreateModal = useCallback(() => {
    setEditingRecord(null);
    form.resetFields();
    setIsModalOpen(true);
  }, [form]);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2>出库管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          创建出库单
        </Button>
      </div>

      <Table columns={columns} dataSource={orders || []} loading={isLoading} rowKey="id" />

      <Modal
        title={editingRecord ? '查看出库单' : '创建出库单'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={editingRecord ? null : [
          <Button key="cancel" onClick={() => setIsModalOpen(false)}>取消</Button>,
          <Button key="submit" type="primary" onClick={() => form.submit()} loading={createMutation.isPending}>确定</Button>,
        ]}
        width={800}
        destroyOnClose={true}
      >
        <Form 
          form={form} 
          layout="vertical" 
          onFinish={handleSubmit}
          initialValues={{ order_type: 'sales', priority: 'normal', items: [] }}
        >
          <Form.Item name="order_type" label="出库类型" rules={[{ required: true }]}>
            <Select disabled={!!editingRecord}>
              <Option value="sales">销售出库</Option>
              <Option value="transfer">调拨出库</Option>
            </Select>
          </Form.Item>
          <Form.Item name="warehouse_id" label="仓库" rules={[{ required: true, message: '请选择仓库' }]}>
            <Select disabled={!!editingRecord} placeholder="选择仓库">
              {warehouses.map((w: any) => (
                <Option key={w.id} value={w.id}>{w.name} ({w.code})</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="priority" label="优先级">
            <Select disabled={!!editingRecord}>
              <Option value="normal">普通</Option>
              <Option value="high">高</Option>
            </Select>
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea disabled={!!editingRecord} />
          </Form.Item>
          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                    <Form.Item {...restField} name={[name, 'sku_id']} rules={[{ required: true, message: '请选择商品' }]}>
                      <Select placeholder="选择商品" disabled={!!editingRecord} style={{ width: 200 }}>
                        {skus.map((s: any) => (
                          <Option key={s.id} value={s.id}>{s.name} ({s.code})</Option>
                        ))}
                      </Select>
                    </Form.Item>
                    <Form.Item {...restField} name={[name, 'expected_qty']} rules={[{ required: true, message: '请输入数量' }]}>
                      <InputNumber placeholder="数量" min={1} disabled={!!editingRecord} />
                    </Form.Item>
                    {!editingRecord && <Button type="link" onClick={() => remove(name)}>删除</Button>}
                  </Space>
                ))}
                {!editingRecord && (
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                    添加商品
                  </Button>
                )}
              </>
            )}
          </Form.List>
        </Form>
      </Modal>
      {/* 状态操作模态框 */}
      <Modal
        title={
          actionType === 'pick' ? '拣货操作' :
          actionType === 'ship' ? '发货操作' : '操作'
        }
        open={isActionModalOpen}
        onCancel={() => {
          setIsActionModalOpen(false);
          setActionFormData(null);
        }}
        footer={[
          <Button key="cancel" onClick={() => { setIsActionModalOpen(false); setActionFormData(null); }}>取消</Button>,
          <Button
            key="submit"
            type="primary"
            onClick={handleActionSubmit}
            loading={pickMutation.isPending || shipMutation.isPending}
          >
            确定
          </Button>,
        ]}
        width={600}
        destroyOnClose
      >
        {actionType === 'pick' && actionRecord && (
          <Form layout="vertical">
            <Form.Item label="出库明细" required>
              <Select
                placeholder="选择出库明细"
                onChange={(value) => {
                  const item = actionRecord.items?.find((i: any) => i.id === value);
                  setActionFormData({ ...actionFormData, outbound_item_id: value, sku_id: item?.sku_id });
                }}
              >
                {actionRecord.items?.map((item: any) => (
                  <Option key={item.id} value={item.id}>
                    {item.sku_name || item.sku_code} (计划: {item.expected_qty}, 已拣: {item.picked_qty || 0})
                  </Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item label="拣货数量" required>
              <InputNumber
                min={1}
                placeholder="输入拣货数量"
                onChange={(value) => setActionFormData({ ...actionFormData, quantity: value })}
              />
            </Form.Item>
            <Form.Item label="来源库位" required>
              <Select
                placeholder="选择来源库位"
                onChange={(value) => setActionFormData({ ...actionFormData, from_location_id: value })}
              >
                {locations.map((loc: any) => (
                  <Option key={loc.id} value={loc.id}>{loc.code} - {loc.name}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item label="操作人">
              <Input
                placeholder="操作人姓名"
                onChange={(e) => setActionFormData({ ...actionFormData, operator: e.target.value })}
              />
            </Form.Item>
          </Form>
        )}

        {actionType === 'ship' && actionRecord && (
          <Form layout="vertical">
            <Form.Item label="出库明细" required>
              <Select
                placeholder="选择出库明细"
                onChange={(value) => {
                  const item = actionRecord.items?.find((i: any) => i.id === value);
                  setActionFormData({ ...actionFormData, outbound_item_id: value, sku_id: item?.sku_id });
                }}
              >
                {actionRecord.items?.map((item: any) => (
                  <Option key={item.id} value={item.id}>
                    {item.sku_name || item.sku_code} (计划: {item.expected_qty}, 已发: {item.shipped_qty || 0})
                  </Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item label="发货数量" required>
              <InputNumber
                min={1}
                placeholder="输入发货数量"
                onChange={(value) => setActionFormData({ ...actionFormData, quantity: value })}
              />
            </Form.Item>
            <Form.Item label="快递单号">
              <Input
                placeholder="输入快递单号"
                onChange={(e) => setActionFormData({ ...actionFormData, tracking_no: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="承运商">
              <Input
                placeholder="输入承运商"
                onChange={(e) => setActionFormData({ ...actionFormData, carrier: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="操作人">
              <Input
                placeholder="操作人姓名"
                onChange={(e) => setActionFormData({ ...actionFormData, operator: e.target.value })}
              />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  );
}
