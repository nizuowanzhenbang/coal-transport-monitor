import React, { useCallback, useEffect, useState } from 'react';
import {
  Card,
  Table,
  Tag,
  Select,
  Button,
  Space,
  Modal,
  Input,
  message,
  Row,
  Col,
  Statistic,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  AlertOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { alertApi, exportApi } from '../api';
import type { AlertRecord, AlertStats, AlertType, Severity, AlertStatus } from '../types';
import dayjs from 'dayjs';

const { TextArea } = Input;

const TYPE_LABELS: Record<AlertType, string> = {
  WEIGHT_SHORTAGE: '亏吨',
  WEIGHT_OVERAGE: '盈吨',
  TIME_EXCESSIVE: '运输超时',
  SEAL_MISMATCH: '铅封不一致',
  SEAL_DAMAGED: '铅封损坏',
};

const TYPE_COLORS: Record<AlertType, string> = {
  WEIGHT_SHORTAGE: '#ff4d4f',
  WEIGHT_OVERAGE: '#faad14',
  TIME_EXCESSIVE: '#1677ff',
  SEAL_MISMATCH: '#ff4d4f',
  SEAL_DAMAGED: '#faad14',
};

const STATUS_MAP: Record<AlertStatus, { color: string; text: string }> = {
  PENDING: { color: 'red', text: '待处理' },
  ACKNOWLEDGED: { color: 'gold', text: '已确认' },
  RESOLVED: { color: 'green', text: '已解决' },
  DISMISSED: { color: 'default', text: '已忽略' },
};

interface Filters {
  alert_type?: AlertType;
  severity?: Severity;
  status?: AlertStatus;
}

const AlertCenter: React.FC = () => {
  const [data, setData] = useState<AlertRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Filters>({});
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [resolveModal, setResolveModal] = useState<{ id: number } | null>(null);
  const [resolveNotes, setResolveNotes] = useState('');

  const fetchData = useCallback(async (p: number, f: Filters) => {
    setLoading(true);
    try {
      const res = await alertApi.list({ page: p, page_size: 20, ...f });
      setData(res.data.items);
      setTotal(res.data.total);
    } catch {
      message.error('预警数据加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await alertApi.stats(30);
      setStats(res.data);
    } catch {
      // 静默失败
    }
  }, []);

  useEffect(() => {
    fetchData(1, {});
    fetchStats();
  }, [fetchData, fetchStats]);

  const applyFilter = useCallback(
    (patch: Partial<Filters>) => {
      const next = { ...filters, ...patch };
      setFilters(next);
      setPage(1);
      fetchData(1, next);
    },
    [filters, fetchData]
  );

  const handleAcknowledge = async (id: number) => {
    try {
      await alertApi.acknowledge(id);
      message.success('已确认');
      fetchData(page, filters);
      fetchStats();
    } catch (err: unknown) {
      message.error((err as { detail?: string })?.detail || '操作失败');
    }
  };

  const handleResolve = async () => {
    if (!resolveModal) return;
    if (!resolveNotes.trim()) {
      message.warning('请填写处理备注');
      return;
    }
    try {
      await alertApi.resolve(resolveModal.id, resolveNotes);
      message.success('已处理');
      setResolveModal(null);
      setResolveNotes('');
      fetchData(page, filters);
      fetchStats();
    } catch (err: unknown) {
      message.error((err as { detail?: string })?.detail || '操作失败');
    }
  };

  const handleDismiss = async (id: number) => {
    try {
      await alertApi.dismiss(id);
      message.success('已忽略');
      fetchData(page, filters);
      fetchStats();
    } catch (err: unknown) {
      message.error((err as { detail?: string })?.detail || '操作失败');
    }
  };

  const columns: ColumnsType<AlertRecord> = [
    {
      title: '类型',
      dataIndex: 'alert_type',
      width: 120,
      render: (v: AlertType) => <Tag color={TYPE_COLORS[v]}>{TYPE_LABELS[v]}</Tag>,
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      width: 90,
      render: (v: Severity) => (
        <Tag
          color={v === 'SEVERE' ? 'red' : 'gold'}
          icon={v === 'SEVERE' ? <WarningOutlined /> : <AlertOutlined />}
        >
          {v === 'SEVERE' ? '严重' : '一般'}
        </Tag>
      ),
    },
    { title: '车牌号', dataIndex: 'plate_number', width: 100 },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    {
      title: '触发值',
      dataIndex: 'actual_value',
      width: 80,
      render: (v: number | null) => (v != null ? v.toFixed(4) : '-'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (v: AlertStatus) => {
        const s = STATUS_MAP[v] ?? { color: 'default', text: v };
        return <Tag color={s.color}>{s.text}</Tag>;
      },
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      width: 130,
      render: (v: string) => dayjs(v).format('MM-DD HH:mm'),
    },
    {
      title: '操作',
      width: 200,
      render: (_: unknown, record: AlertRecord) => (
        <Space size="small">
          {record.status === 'PENDING' && (
            <>
              <Button size="small" type="primary" onClick={() => handleAcknowledge(record.id)}>
                确认
              </Button>
              <Button size="small" onClick={() => setResolveModal({ id: record.id })}>
                处理
              </Button>
              <Button size="small" danger onClick={() => handleDismiss(record.id)}>
                忽略
              </Button>
            </>
          )}
          {record.status === 'ACKNOWLEDGED' && (
            <Button size="small" onClick={() => setResolveModal({ id: record.id })}>
              处理
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const pieOption = stats
    ? {
        tooltip: { trigger: 'item' as const },
        series: [
          {
            type: 'pie',
            radius: ['40%', '70%'],
            data: Object.entries(stats.by_type ?? {}).map(([k, v]) => ({
              name: TYPE_LABELS[k as AlertType] ?? k,
              value: v,
            })),
            label: { show: true, formatter: '{b}: {c}' },
          },
        ],
      }
    : null;

  return (
    <div>
      {stats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic title="预警总数" value={stats.total} prefix={<AlertOutlined />} />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="待处理"
                value={stats.by_status?.PENDING ?? 0}
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<WarningOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="已解决"
                value={stats.by_status?.RESOLVED ?? 0}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="严重预警"
                value={stats.by_severity?.SEVERE ?? 0}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {pieOption && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} md={10}>
            <Card title="预警类型分布" size="small">
              <ReactECharts option={pieOption} style={{ height: 220 }} />
            </Card>
          </Col>
        </Row>
      )}

      <Card
        extra={
          <Button
            icon={<DownloadOutlined />}
            size="small"
            onClick={() =>
              exportApi.alerts({
                severity: filters.severity,
                alert_status: filters.status,
                alert_type: filters.alert_type,
              })
            }
          >
            导出 CSV
          </Button>
        }
      >
        <Space wrap style={{ marginBottom: 16 }}>
          <Select
            placeholder="预警类型"
            allowClear
            style={{ width: 130 }}
            onChange={(v: AlertType | undefined) => applyFilter({ alert_type: v })}
            options={Object.entries(TYPE_LABELS).map(([k, v]) => ({ value: k, label: v }))}
          />
          <Select
            placeholder="严重程度"
            allowClear
            style={{ width: 110 }}
            onChange={(v: Severity | undefined) => applyFilter({ severity: v })}
            options={[
              { value: 'GENERAL', label: '一般' },
              { value: 'SEVERE', label: '严重' },
            ]}
          />
          <Select
            placeholder="处理状态"
            allowClear
            style={{ width: 110 }}
            onChange={(v: AlertStatus | undefined) => applyFilter({ status: v })}
            options={Object.entries(STATUS_MAP).map(([k, v]) => ({ value: k, label: v.text }))}
          />
        </Space>

        <Table<AlertRecord>
          dataSource={data}
          columns={columns}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1000 }}
          pagination={{
            current: page,
            pageSize: 20,
            total,
            showTotal: (t) => `共 ${t} 条预警`,
            onChange: (p) => {
              setPage(p);
              fetchData(p, filters);
            },
          }}
        />
      </Card>

      <Modal
        title="处理预警"
        open={!!resolveModal}
        onCancel={() => {
          setResolveModal(null);
          setResolveNotes('');
        }}
        onOk={handleResolve}
        okText="确认处理"
      >
        <TextArea
          rows={4}
          placeholder="请填写处理备注..."
          value={resolveNotes}
          onChange={(e) => setResolveNotes(e.target.value)}
        />
      </Modal>
    </div>
  );
};

export default AlertCenter;
