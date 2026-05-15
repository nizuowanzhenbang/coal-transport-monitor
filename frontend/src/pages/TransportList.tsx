import React, { useCallback, useEffect, useState } from 'react';
import {
  Card,
  Table,
  Tag,
  Input,
  Select,
  DatePicker,
  Button,
  Space,
  Modal,
  Descriptions,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { SearchOutlined, ReloadOutlined, EyeOutlined, DownloadOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import { transportApi, exportApi } from '../api';
import type { TransportListItem, TransportDetail, RecordStatus } from '../types';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

const STATUS_COLORS: Record<RecordStatus, string> = {
  NORMAL: 'green',
  ALERT: 'gold',
  SEVERE: 'red',
};
const STATUS_LABELS: Record<RecordStatus, string> = {
  NORMAL: '正常',
  ALERT: '一般预警',
  SEVERE: '严重预警',
};

interface Filters {
  plate?: string;
  status?: RecordStatus;
  dates?: [Dayjs, Dayjs] | null;
}

const TransportList: React.FC = () => {
  const [data, setData] = useState<TransportListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState<Filters>({});
  const [detail, setDetail] = useState<TransportDetail | null>(null);

  const fetchData = useCallback(async (p: number, ps: number, f: Filters) => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page: p, page_size: ps };
      if (f.plate) params.plate = f.plate;
      if (f.status) params.status = f.status;
      if (f.dates?.[0]) params.start_date = f.dates[0].toISOString();
      if (f.dates?.[1]) params.end_date = f.dates[1].toISOString();
      const res = await transportApi.list(params as Parameters<typeof transportApi.list>[0]);
      setData(res.data.items);
      setTotal(res.data.total);
    } catch {
      message.error('数据加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(1, 20, {});
  }, [fetchData]);

  const showDetail = async (id: number) => {
    try {
      const res = await transportApi.get(id);
      setDetail(res.data);
    } catch {
      message.error('获取详情失败');
    }
  };

  const handleExport = () => {
    exportApi.transports({
      status: filters.status,
      plate: filters.plate,
      start_date: filters.dates?.[0]?.toISOString(),
      end_date: filters.dates?.[1]?.toISOString(),
    });
  };

  const columns: ColumnsType<TransportListItem> = [
    { title: '车牌号', dataIndex: 'plate_number', width: 100 },
    { title: '出发港口', dataIndex: 'departure_port', width: 120 },
    {
      title: '出港时间',
      dataIndex: 'departure_time',
      width: 150,
      render: (v: string | null) => (v ? dayjs(v).format('MM-DD HH:mm') : '-'),
    },
    {
      title: '到达时间',
      dataIndex: 'arrival_time',
      width: 150,
      render: (v: string | null) => (v ? dayjs(v).format('MM-DD HH:mm') : '-'),
    },
    {
      title: '出港净重(t)',
      dataIndex: 'departure_net_weight',
      width: 100,
      render: (v: number | null) => (v ? (v / 1000).toFixed(2) : '-'),
    },
    {
      title: '进厂净重(t)',
      dataIndex: 'arrival_net_weight',
      width: 100,
      render: (v: number | null) => (v ? (v / 1000).toFixed(2) : '-'),
    },
    {
      title: '偏差率',
      dataIndex: 'weight_diff_ratio',
      width: 100,
      render: (v: number | null) => {
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
      render: (v: number | null) => (v ? `${v}分` : '-'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (v: RecordStatus) => <Tag color={STATUS_COLORS[v]}>{STATUS_LABELS[v]}</Tag>,
    },
    {
      title: '操作',
      width: 60,
      render: (_: unknown, record: TransportListItem) => (
        <Button type="link" icon={<EyeOutlined />} onClick={() => showDetail(record.id)} />
      ),
    },
  ];

  return (
    <div>
      <Card
        extra={
          <Button icon={<DownloadOutlined />} size="small" onClick={handleExport}>
            导出 CSV
          </Button>
        }
      >
        <Space wrap style={{ marginBottom: 16 }}>
          <Input
            placeholder="车牌号"
            prefix={<SearchOutlined />}
            style={{ width: 140 }}
            onChange={(e) => setFilters((f) => ({ ...f, plate: e.target.value }))}
            onPressEnter={() => {
              setPage(1);
              fetchData(1, pageSize, filters);
            }}
          />
          <Select
            placeholder="状态"
            allowClear
            style={{ width: 120 }}
            onChange={(v: RecordStatus | undefined) => {
              const next = { ...filters, status: v };
              setFilters(next);
              setPage(1);
              fetchData(1, pageSize, next);
            }}
            options={Object.entries(STATUS_LABELS).map(([k, v]) => ({ value: k, label: v }))}
          />
          <RangePicker
            onChange={(v) => {
              const next = { ...filters, dates: v as [Dayjs, Dayjs] | null };
              setFilters(next);
              setPage(1);
              fetchData(1, pageSize, next);
            }}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              setFilters({});
              setPage(1);
              fetchData(1, pageSize, {});
            }}
          >
            重置
          </Button>
        </Space>

        <Table<TransportListItem>
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
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
              fetchData(p, ps, filters);
            },
          }}
        />
      </Card>

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
            <Descriptions.Item label="出港时间">
              {detail.departure_time
                ? dayjs(detail.departure_time).format('YYYY-MM-DD HH:mm')
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="到达时间">
              {detail.arrival_time
                ? dayjs(detail.arrival_time).format('YYYY-MM-DD HH:mm')
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="出港毛重">
              {detail.departure_weight
                ? `${(detail.departure_weight / 1000).toFixed(2)} 吨`
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="进厂毛重">
              {detail.arrival_weight ? `${(detail.arrival_weight / 1000).toFixed(2)} 吨` : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="出港净重">
              {detail.departure_net_weight
                ? `${(detail.departure_net_weight / 1000).toFixed(2)} 吨`
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="进厂净重">
              {detail.arrival_net_weight
                ? `${(detail.arrival_net_weight / 1000).toFixed(2)} 吨`
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="重量差">
              {detail.weight_diff ? `${(detail.weight_diff / 1000).toFixed(3)} 吨` : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="偏差率">
              <Tag color={Math.abs(detail.weight_diff_ratio ?? 0) > 0.003 ? 'red' : 'green'}>
                {detail.weight_diff_ratio != null
                  ? `${(detail.weight_diff_ratio * 1000).toFixed(1)}‰`
                  : '-'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="运输时长">{detail.transport_duration} 分钟</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={STATUS_COLORS[detail.status]}>{STATUS_LABELS[detail.status]}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="预警" span={2}>
              {detail.alerts?.length > 0 ? (
                detail.alerts.map((a) => (
                  <Tag
                    key={a.id}
                    color={a.severity === 'SEVERE' ? 'red' : 'gold'}
                    style={{ marginBottom: 4 }}
                  >
                    {a.description}
                  </Tag>
                ))
              ) : (
                <Tag color="green">无预警</Tag>
              )}
            </Descriptions.Item>
            {detail.notes && (
              <Descriptions.Item label="备注" span={2}>
                {detail.notes}
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default TransportList;
