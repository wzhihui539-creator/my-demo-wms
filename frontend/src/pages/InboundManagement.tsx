import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Modal, Form, Input, Select, InputNumber, message, Space, Tag } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PlusOutlined, EditOutlined, EyeOutlined, PlayCircleOutlined, CheckCircleOutlined, ArrowUpOutlined } from '@ant-design/icons';
import { api } from '../utils/api';

const { Option } = Select;

interface InboundItem {
  id?: string;
  sku_id: string;
  sku_name?: string;
  sku_code?: string;
  expected_qty: number;
  received_qty?: number;
  putaway_qty?: number;
  status?: string;
}

interface InboundOrder {
  id: string;
  order_no: string;
  order_type: 'purchase' | 'return';
  warehouse_id: string;
  total_qty: number;
  received_qty?: number;
  putaway_qty?: number;
  status: string;
  remark?: string;
  items: InboundItem[];
  created_at: string;
}

export default function InboundManagement() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<InboundOrder | null>(null);
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

  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['inbound-orders'],
    queryFn: async () => {
      try {
        const res = await api.get('/inbound/orders');
        // 确保返回数组
        if (Array.isArray(res.data)) {
          return res.data;
        }
        if (res.data && Array.isArray(res.data.items)) {
          return res.data.items;
        }
        return [];
      } catch (err) {
        console.error('获取入库单失败:', err);
        return [];
      }
    },
    initialData: [],
  });

  useEffect(() => {
    if (error) {
      message.error('加载失败: ' + error.message);
    }
  }, [error]);

  // 收货操作
  const receiveMutation = useMutation({
    mutationFn: ({ orderId, data }: { orderId: string; data: any }) =>
      api.post(`/inbound/orders/${orderId}/receive`, data),
    onSuccess: () => {
      message.success('收货成功');
      queryClient.invalidateQueries({ queryKey: ['inbound-orders'] });
      queryClient.invalidateQueries({ queryKey: ['inventories'] });
      setIsActionModalOpen(false);
      setActionFormData(null);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '收货失败');
    },
  });

  // 完成收货（更新订单状态为 received）
  const completeReceiveMutation = useMutation({
    mutationFn: (orderId: string) =>
      api.post(`/inbound/orders/${orderId}/complete-receive`),
    onSuccess: () => {
      message.success('收货完成');
      queryClient.invalidateQueries({ queryKey: ['inbound-orders'] });
      setIsActionModalOpen(false);
      setActionFormData(null);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '完成收货失败');
    },
  });

  // 创建上架任务
  const putawayTaskMutation = useMutation({
    mutationFn: ({ orderId, data }: { orderId: string; data: any }) =>
      api.post(`/inbound/orders/${orderId}/putaway-tasks`, data),
    onSuccess: () => {
      message.success('上架任务创建成功');
      queryClient.invalidateQueries({ queryKey: ['inbound-orders'] });
      setIsActionModalOpen(false);
      setActionFormData(null);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '创建上架任务失败');
    },
  });

  // 完成上架
  const completePutawayMutation = useMutation({
    mutationFn: ({ taskId, operator }: { taskId: string; operator?: string }) =>
      api.post(`/putaway-tasks/${taskId}/complete`, null, { params: { operator } }),
    onSuccess: () => {
      message.success('上架完成');
      queryClient.invalidateQueries({ queryKey: ['inbound-orders'] });
      queryClient.invalidateQueries({ queryKey: ['inventories'] });
      setIsActionModalOpen(false);
      setActionFormData(null);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '完成上架失败');
    },
  });

  const createMutation = useMutation({
    mutationFn: (data) => api.post('/inbound/orders', data),
    onSuccess: () => {
      message.success('创建成功');
      setIsModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['inbound-orders'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '创建失败');
    },
  });

  const [isActionModalOpen, setIsActionModalOpen] = useState(false);
  const [actionType, setActionType] = useState<'receive' | 'putaway' | 'completePutaway' | 'completeReceive' | null>(null);
  const [actionRecord, setActionRecord] = useState<InboundOrder | null>(null);
  const [actionFormData, setActionFormData] = useState<any>(null);

  const statusColors: Record<string, string> = {
    pending: 'default',
    receiving: 'processing',
    received: 'warning',
    putaway: 'warning',
    completed: 'success',
    cancelled: 'error',
  };

  const statusLabels: Record<string, string> = {
    pending: '待处理',
    receiving: '收货中',
    received: '已收货',
    putaway: '上架中',
    completed: '已完成',
    cancelled: '已取消',
  };

  const getNextAction = (record: InboundOrder) => {
    switch (record.status) {
      case 'pending':
        return { type: 'receive' as const, label: '开始收货', icon: <PlayCircleOutlined /> };
      case 'receiving':
        // 检查是否全部收完
        const allReceived = record.items?.every((item: any) => (item.received_qty || 0) >= item.expected_qty);
        if (allReceived) {
          return { type: 'completeReceive' as const, label: '完成收货', icon: <CheckCircleOutlined /> };
        }
        return { type: 'receive' as const, label: '继续收货', icon: <CheckCircleOutlined /> };
      case 'received':
        return { type: 'putaway' as const, label: '开始上架', icon: <ArrowUpOutlined /> };
      case 'putaway':
        return { type: 'completePutaway' as const, label: '完成上架', icon: <CheckCircleOutlined /> };
      default:
        return null;
    }
  };

  const handleAction = (record: InboundOrder, type: 'receive' | 'putaway' | 'completePutaway' | 'completeReceive') => {
    setActionRecord(record);
    setActionType(type);
    setActionFormData({});
    setIsActionModalOpen(true);
  };

  const handleActionSubmit = () => {
    if (!actionRecord || !actionFormData) return;

    if (actionType === 'receive') {
      receiveMutation.mutate({ orderId: actionRecord.id, data: actionFormData });
    } else if (actionType === 'completeReceive') {
      completeReceiveMutation.mutate(actionRecord.id);
    } else if (actionType === 'putaway') {
      putawayTaskMutation.mutate({ orderId: actionRecord.id, data: actionFormData });
    } else if (actionType === 'completePutaway') {
      completePutawayMutation.mutate({ taskId: actionFormData.task_id, operator: actionFormData.operator });
    }
  };

  const columns = [
    { title: '入库单号', dataIndex: 'order_no', key: 'order_no' },
    { title: '类型', dataIndex: 'order_type', key: 'order_type', render: (type: string) => type === 'purchase' ? '采购入库' : '退货入库' },
    { title: '仓库', dataIndex: 'warehouse_id', key: 'warehouse_id' },
    { title: '总数量', dataIndex: 'total_qty', key: 'total_qty' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (status: string) => <Tag color={statusColors[status]}>{statusLabels[status]}</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: InboundOrder) => {
        const nextAction = getNextAction(record);
        return (
          <Space>
            <Button icon={<EyeOutlined />} size="small" onClick={() => handleView(record)}>查看</Button>
            {record.status === 'pending' && (
              <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)}>编辑</Button>
            )}
            {nextAction && (
              <Button
                type="primary"
                size="small"
                icon={nextAction.icon}
                onClick={() => handleAction(record, nextAction.type)}
              >
                {nextAction.label}
              </Button>
            )}
          </Space>
        );
      },
    },
  ];

  const handleView = useCallback((record: InboundOrder) => {
    setEditingRecord(record);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((record: InboundOrder) => {
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
        <h2>入库管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          创建入库单
        </Button>
      </div>

      <Table 
        columns={columns} 
        dataSource={orders || []} 
        loading={isLoading} 
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingRecord ? '查看入库单' : '创建入库单'}
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
          initialValues={{ order_type: 'purchase', items: [] }}
        >
          <Form.Item name="order_type" label="入库类型" rules={[{ required: true }]}>
            <Select disabled={!!editingRecord}>
              <Option value="purchase">采购入库</Option>
              <Option value="return">退货入库</Option>
            </Select>
          </Form.Item>
          <Form.Item name="warehouse_id" label="仓库" rules={[{ required: true, message: '请选择仓库' }]}>
            <Select disabled={!!editingRecord} placeholder="选择仓库">
              {warehouses.map((w: any) => (
                <Option key={w.id} value={w.id}>{w.name} ({w.code})</Option>
              ))}
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
          actionType === 'receive' ? '收货操作' :
          actionType === 'completeReceive' ? '完成收货' :
          actionType === 'putaway' ? '创建上架任务' :
          actionType === 'completePutaway' ? '完成上架' : '操作'
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
            loading={receiveMutation.isPending || completeReceiveMutation.isPending || putawayTaskMutation.isPending || completePutawayMutation.isPending}
          >
            确定
          </Button>,
        ]}
        width={600}
        destroyOnClose
      >
        {actionType === 'receive' && actionRecord && (
          <Form layout="vertical">
            <Form.Item label="入库明细" required>
              <Select
                placeholder="选择入库明细"
                onChange={(value) => {
                  const item = actionRecord.items?.find((i: any) => i.id === value);
                  setActionFormData({ ...actionFormData, inbound_item_id: value, sku_id: item?.sku_id });
                }}
              >
                {actionRecord.items?.map((item: any) => (
                  <Option key={item.id} value={item.id}>
                    {item.sku_name || item.sku_code} (计划: {item.expected_qty}, 已收: {item.received_qty || 0})
                  </Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item label="收货数量" required>
              <InputNumber
                min={1}
                max={actionRecord.items?.find((i: any) => i.id === actionFormData?.inbound_item_id)?.expected_qty - (actionRecord.items?.find((i: any) => i.id === actionFormData?.inbound_item_id)?.received_qty || 0)}
                placeholder="输入收货数量"
                onChange={(value) => setActionFormData({ ...actionFormData, quantity: value })}
              />
            </Form.Item>
            <Form.Item label="暂存库位">
              <Select
                placeholder="选择暂存库位"
                onChange={(value) => setActionFormData({ ...actionFormData, location_id: value })}
              >
                {locations.map((loc: any) => (
                  <Option key={loc.id} value={loc.id}>{loc.code} - {loc.name}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item label="批次号">
              <Input
                placeholder="输入批次号"
                onChange={(e) => setActionFormData({ ...actionFormData, lot_no: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="质检状态">
              <Select
                defaultValue="pass"
                onChange={(value) => setActionFormData({ ...actionFormData, quality_status: value })}
              >
                <Option value="pass">合格</Option>
                <Option value="reject">不合格</Option>
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

        {actionType === 'completeReceive' && actionRecord && (
          <div style={{ padding: '20px 0' }}>
            <p>确认完成收货？</p>
            <p>入库单号: {actionRecord.order_no}</p>
            <p>总数量: {actionRecord.total_qty}</p>
            <p>已收货: {actionRecord.received_qty || 0}</p>
          </div>
        )}

        {actionType === 'putaway' && actionRecord && (
          <Form layout="vertical">
            <Form.Item label="目标库位" required>
              <Select
                placeholder="选择上架库位"
                onChange={(value) => setActionFormData({ ...actionFormData, to_location_id: value })}
              >
                {locations.map((loc: any) => (
                  <Option key={loc.id} value={loc.id}>{loc.code} - {loc.name}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item label="收货记录ID" required>
              <Input
                placeholder="收货记录ID"
                onChange={(e) => setActionFormData({ ...actionFormData, receive_record_id: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="上架数量" required>
              <InputNumber
                min={1}
                placeholder="输入上架数量"
                onChange={(value) => setActionFormData({ ...actionFormData, quantity: value })}
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

        {actionType === 'completePutaway' && (
          <Form layout="vertical">
            <Form.Item label="上架任务ID" required>
              <Input
                placeholder="上架任务ID"
                onChange={(e) => setActionFormData({ ...actionFormData, task_id: e.target.value })}
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