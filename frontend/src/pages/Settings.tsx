import React, { useState } from 'react';
import { Card, Form, Input, Button, message, Tabs, Table, Modal, Space } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PlusOutlined } from '@ant-design/icons';
import { api } from '../utils/api';

export default function Settings() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('1');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState<'warehouse' | 'sku'>('warehouse');
  const [form] = Form.useForm();

  const { data: warehouses, isLoading: warehousesLoading } = useQuery({
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

  const { data: skus, isLoading: skusLoading } = useQuery({
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

  const createWarehouseMutation = useMutation({
    mutationFn: (data: any) => api.post('/warehouses', data),
    onSuccess: () => {
      message.success('仓库创建成功');
      setIsModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['warehouses'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '创建失败');
    },
  });

  const createSkuMutation = useMutation({
    mutationFn: (data: any) => api.post('/skus', data),
    onSuccess: () => {
      message.success('商品创建成功');
      setIsModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['skus'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '创建失败');
    },
  });

  const warehouseColumns = [
    { title: '编码', dataIndex: 'code', key: 'code' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '地址', dataIndex: 'address', key: 'address' },
    { title: '联系人', dataIndex: 'contact', key: 'contact' },
    { title: '电话', dataIndex: 'phone', key: 'phone' },
    { title: '状态', dataIndex: 'status', key: 'status' },
  ];

  const skuColumns = [
    { title: '编码', dataIndex: 'code', key: 'code' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '条码', dataIndex: 'barcode', key: 'barcode' },
    { title: '规格', dataIndex: 'spec', key: 'spec' },
    { title: '单位', dataIndex: 'unit', key: 'unit' },
    { title: '分类', dataIndex: 'category', key: 'category' },
    { title: '品牌', dataIndex: 'brand', key: 'brand' },
    { title: '状态', dataIndex: 'status', key: 'status' },
  ];

  const handleSubmit = (values: any) => {
    if (modalType === 'warehouse') {
      createWarehouseMutation.mutate(values);
    } else {
      createSkuMutation.mutate(values);
    }
  };

  const openModal = (type: 'warehouse' | 'sku') => {
    setModalType(type);
    form.resetFields();
    setIsModalOpen(true);
  };

  return (
    <div>
      <h2>系统设置</h2>
      
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: '1',
            label: '仓库管理',
            children: (
              <Card>
                <div style={{ marginBottom: 16 }}>
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal('warehouse')}>
                    新建仓库
                  </Button>
                </div>
                <Table
                  dataSource={warehouses || []}
                  columns={warehouseColumns}
                  rowKey="id"
                  loading={warehousesLoading}
                />
              </Card>
            ),
          },
          {
            key: '2',
            label: 'SKU管理',
            children: (
              <Card>
                <div style={{ marginBottom: 16 }}>
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal('sku')}>
                    新建商品
                  </Button>
                </div>
                <Table
                  dataSource={skus || []}
                  columns={skuColumns}
                  rowKey="id"
                  loading={skusLoading}
                />
              </Card>
            ),
          },
          {
            key: '3',
            label: '用户管理',
            children: (
              <Card>
                <p>用户管理功能开发中...</p>
              </Card>
            ),
          },
        ]}
      />

      <Modal
        title={modalType === 'warehouse' ? '新建仓库' : '新建商品'}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={[
          <Button key="cancel" onClick={() => setIsModalOpen(false)}>取消</Button>,
          <Button 
            key="submit" 
            type="primary" 
            onClick={() => form.submit()}
            loading={modalType === 'warehouse' ? createWarehouseMutation.isPending : createSkuMutation.isPending}
          >
            确定
          </Button>,
        ]}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {modalType === 'warehouse' ? (
            <>
              <Form.Item name="code" label="仓库编码" rules={[{ required: true, message: '请输入仓库编码' }]}>
                <Input placeholder="如：WH001" />
              </Form.Item>
              <Form.Item name="name" label="仓库名称" rules={[{ required: true, message: '请输入仓库名称' }]}>
                <Input placeholder="如：主仓库" />
              </Form.Item>
              <Form.Item name="address" label="地址">
                <Input placeholder="仓库地址" />
              </Form.Item>
              <Form.Item name="contact" label="联系人">
                <Input placeholder="联系人姓名" />
              </Form.Item>
              <Form.Item name="phone" label="电话">
                <Input placeholder="联系电话" />
              </Form.Item>
            </>
          ) : (
            <>
              <Form.Item name="code" label="商品编码" rules={[{ required: true, message: '请输入商品编码' }]}>
                <Input placeholder="如：SKU001" />
              </Form.Item>
              <Form.Item name="name" label="商品名称" rules={[{ required: true, message: '请输入商品名称' }]}>
                <Input placeholder="如：iPhone 15 Pro" />
              </Form.Item>
              <Form.Item name="barcode" label="条码">
                <Input placeholder="商品条码" />
              </Form.Item>
              <Form.Item name="spec" label="规格">
                <Input placeholder="如：128GB 黑色" />
              </Form.Item>
              <Form.Item name="unit" label="单位" rules={[{ required: true, message: '请输入单位' }]}>
                <Input placeholder="如：件、个、箱" />
              </Form.Item>
              <Form.Item name="category" label="分类">
                <Input placeholder="商品分类" />
              </Form.Item>
              <Form.Item name="brand" label="品牌">
                <Input placeholder="品牌名称" />
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </div>
  );
}