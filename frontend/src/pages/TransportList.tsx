import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Input, Select, DatePicker, Button, Space, Modal, Descriptions, message } from 'antd';
import { SearchOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { transportApi } from '../api';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

const statusColors: Record<string, string> = {
  NORMAL: 'green',
  ALERT: 'gold',
  SEVERE: 'red',
};
const statusLabels: Record<string, string> = {
  NORMAL: '正常',
  ALERT: '一般预警',
  SEVERE: '严重预警',
};

const TransportList: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState<any>({});
  const [detail, setDetail] = useState<any>(null);

  const fetchData = async (p = page, ps = pageSize, f = filters) => {
    setLoading(true);
    try {
      const params: any = { page: p, page_size: ps };
      if (f.plate) params.plate = f.plate;
      if (f.status) params.status = f.status;
      if (f.dates?.length === 2) {
        params.start_date = f.dates[0].toISOString();
        params.end_date = f.dates[1].toISOString();
      }
      const res: any = await transportApi.list(params);
      setData(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      message.error('数据加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const showDetail = async (id: number) => {
    try {
      const res: any = await transportApi.get(id);
      setDetail(res.data);
    } catch {
      message.error('获取详情失败');
    }
  };

  const columns = [
    { title: '车牌号', dataIndex: 'plate_number', width: 100 },
    { title: '出发港口', dataIndex: 'departure_port', width: 120 },
    {
      title: '出港时间',
      dataIndex: 'departure_time',
      width: 150,
      render: (v: string) => v ? dayjs(v).format('MM-DD HH:mm') : '-',
    },
    {
      title: '到达时间',
      dataIndex: 'arrival_time',
      width: 150,
      render: (v: string) => v ? dayjs(v).format('MM-DD HH:mm') : '-',
    },
    {
      title: '出港净重(t)',
      dataIndex: 'departure_net_weight',
      width: 100,
      render: (v: number) => v ? (v / 1000).toFixed(2) : '-',
    },
    {
      title: '进厂净重(t)',
      dataIndex: 'arrival_net_weight',
      width: 100,
      render: (v: number) => v ? (v / 1000).toFixed(2) : '-',
    },
    {
      title: '偏差率',
      dataIndex: 'weight_diff_ratio',
      width: 100,
      render: (v: number) => {
        if (v == null) return '-';
        const pct = (v * 1000).toFixed(1);
        const color = Math.abs(v) > 0.003 ? 'red' : Math.abs(v) > 0.002 ? 'gold' : 'green';
        return <Tag color={color}>{pct}‰</Tag>;
      },
    },
    {
      title: '运输时长',
      dataIndex: 'transport_duration',
      width: 90,
      render: (v: number) => v ? `${v}分` : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (v: string) => <Tag color={statusColors[v]}>{statusLabels[v]}</Tag>,
    },
    {
      title: '操作',
      width: 60,
      render: (_: any, record: any) => (
        <Button type="link" icon={<EyeOutlined />} onClick={() => showDetail(record.id)} />
      ),
    },
  ];

  return (
    <div>
      <Card>
        {/* 筛选栏 */}
        <Space wrap style={{ marginBottom: 16 }}>
          <Input
            placeholder="车牌号"
            prefix={<SearchOutlined />}
            style={{ width: 140 }}
            onChange={(e) => setFilters((f: any) => ({ ...f, plate: e.target.value }))}
            onPressEnter={() => fetchData(1)}
          />
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 120 }}
            onChange={(v) => {
              setFilters((f: any) => ({ ...f, status: v }));
              setTimeout(() => fetchData(1), 0);
            }}
            options={[
              { value: 'NORMAL', label: '正常' },
              { value: 'ALERT', label: '一般预警' },
              { value: 'SEVERE', label: '严重预警' },
            ]}
          />
          <RangePicker
            onChange={(v) => {
              setFilters((f: any) => ({ ...f, dates: v }));
              setTimeout(() => fetchData(1), 0);
            }}
          />
          <Button icon={<ReloadOutlined />} onClick={() => { setFilters({}); fetchData(1, 20, {}); }}>
            重置
          </Button>
        </Space>

        {/* 数据表格 */}
        <Table
          dataSource={data}
          columns={columns}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1100 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条记录`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps); fetchData(p, ps); },
          }}
        />
      </Card>

      {/* 详情弹窗 */}
      <Modal
        title="运输记录详情"
        open={!!detail}
        onCancel={() => setDetail(null)}
        footer={null}
        width={700}
      >
        {detail && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="车牌号">{detail.plate_number}</Descriptions.Item>
            <Descriptions.Item label="出发港口">{detail.departure_port}</Descriptions.Item>
            <Descriptions.Item label="出港时间">{detail.departure_time ? dayjs(detail.departure_time).format('YYYY-MM-DD HH:mm') : '-'}</Descriptions.Item>
            <Descriptions.Item label="到达时间">{detail.arrival_time ? dayjs(detail.arrival_time).format('YYYY-MM-DD HH:mm') : '-'}</Descriptions.Item>
            <Descriptions.Item label="出港毛重">{detail.departure_weight ? `${(detail.departure_weight / 1000).toFixed(2)} 吨` : '-'}</Descriptions.Item>
            <Descriptions.Item label="进厂毛重">{detail.arrival_weight ? `${(detail.arrival_weight / 1000).toFixed(2)} 吨` : '-'}</Descriptions.Item>
            <Descriptions.Item label="出港净重">{detail.departure_net_weight ? `${(detail.departure_net_weight / 1000).toFixed(2)} 吨` : '-'}</Descriptions.Item>
            <Descriptions.Item label="进厂净重">{detail.arrival_net_weight ? `${(detail.arrival_net_weight / 1000).toFixed(2)} 吨` : '-'}</Descriptions.Item>
            <Descriptions.Item label="重量差">{detail.weight_diff ? `${(detail.weight_diff / 1000).toFixed(3)} 吨` : '-'}</Descriptions.Item>
            <Descriptions.Item label="偏差率">
              <Tag color={Math.abs(detail.weight_diff_ratio || 0) > 0.003 ? 'red' : 'green'}>
                {detail.weight_diff_ratio != null ? `${(detail.weight_diff_ratio * 1000).toFixed(1)}‰` : '-'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="运输时长">{detail.transport_duration} 分钟</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusColors[detail.status]}>{statusLabels[detail.status]}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="预警" span={2}>
              {detail.alerts?.length > 0 ? (
                detail.alerts.map((a: any) => (
                  <Tag key={a.id} color={a.severity === 'SEVERE' ? 'red' : 'gold'} style={{ marginBottom: 4 }}>
                    {a.description}
                  </Tag>
                ))
              ) : (
                <Tag color="green">无预警</Tag>
              )}
            </Descriptions.Item>
            {detail.notes && <Descriptions.Item label="备注" span={2}>{detail.notes}</Descriptions.Item>}
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default TransportList;
