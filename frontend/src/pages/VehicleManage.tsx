import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Input, Button, Space, Modal, Form, InputNumber, message } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined } from '@ant-design/icons';
import { vehicleApi } from '../api';
import dayjs from 'dayjs';

const VehicleManage: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [addModal, setAddModal] = useState(false);
  const [editModal, setEditModal] = useState<any>(null);
  const [form] = Form.useForm();

  const fetchData = async (p = page) => {
    setLoading(true);
    try {
      const res: any = await vehicleApi.list({ page: p, page_size: 20 });
      setData(res.data.items);
      setTotal(res.data.total);
    } catch {
      message.error('数据加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleAdd = async () => {
    try {
      const values = await form.validateFields();
      await vehicleApi.create(values);
      message.success('车辆添加成功');
      setAddModal(false);
      form.resetFields();
      fetchData(1);
    } catch (err: any) {
      if (err?.detail) message.error(err.detail);
    }
  };

  const handleEdit = async () => {
    try {
      const values = await form.validateFields();
      await vehicleApi.update(editModal.id, values);
      message.success('更新成功');
      setEditModal(null);
      form.resetFields();
      fetchData();
    } catch (err: any) {
      if (err?.detail) message.error(err.detail);
    }
  };

  const openEdit = (record: any) => {
    setEditModal(record);
    form.setFieldsValue(record);
  };

  const columns = [
    { title: '车牌号', dataIndex: 'plate_number', width: 110 },
    { title: '司机', dataIndex: 'driver_name', width: 80 },
    { title: '电话', dataIndex: 'driver_phone', width: 120 },
    {
      title: '皮重',
      dataIndex: 'tare_weight',
      width: 100,
      render: (v: number) => v ? `${(v / 1000).toFixed(2)} 吨` : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (v: string) => <Tag color={v === 'ACTIVE' ? 'green' : 'default'}>{v === 'ACTIVE' ? '运营中' : '已停用'}</Tag>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 130,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-',
    },
    {
      title: '操作',
      width: 60,
      render: (_: any, record: any) => (
        <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(record)} />
      ),
    },
  ];

  return (
    <Card
      title="车辆管理"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setAddModal(true); form.resetFields(); }}>
          新增车辆
        </Button>
      }
    >
      <Table
        dataSource={data}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize: 20,
          total,
          showTotal: (t) => `共 ${t} 辆车`,
          onChange: (p) => { setPage(p); fetchData(p); },
        }}
      />

      {/* 新增/编辑弹窗 */}
      <Modal
        title={editModal ? '编辑车辆' : '新增车辆'}
        open={addModal || !!editModal}
        onCancel={() => { setAddModal(false); setEditModal(null); form.resetFields(); }}
        onOk={editModal ? handleEdit : handleAdd}
        okText="保存"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="plate_number" label="车牌号" rules={[{ required: true, message: '请输入车牌号' }]}>
            <Input placeholder="如：粤A12345" disabled={!!editModal} />
          </Form.Item>
          <Form.Item name="driver_name" label="司机姓名" rules={[{ required: true, message: '请输入司机姓名' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="driver_phone" label="司机电话">
            <Input />
          </Form.Item>
          <Form.Item
            name="tare_weight"
            label="皮重(kg)"
            rules={[{ required: true, message: '请输入皮重' }]}
          >
            <InputNumber min={8000} max={20000} style={{ width: '100%' }} placeholder="8000 ~ 20000" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default VehicleManage;
