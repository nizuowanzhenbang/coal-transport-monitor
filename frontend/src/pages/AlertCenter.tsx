import React, { useEffect, useState } from 'react';
import { Card, Table, Tag, Select, Button, Space, Modal, Input, message, Row, Col, Statistic } from 'antd';
import {
  AlertOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { alertApi } from '../api';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';

const { TextArea } = Input;

const typeLabels: Record<string, string> = {
  WEIGHT_SHORTAGE: '亏吨',
  WEIGHT_OVERAGE: '盈吨',
  TIME_EXCESSIVE: '运输超时',
  SEAL_MISMATCH: '铅封不一致',
  SEAL_DAMAGED: '铅封损坏',
};
const typeColors: Record<string, string> = {
  WEIGHT_SHORTAGE: '#ff4d4f',
  WEIGHT_OVERAGE: '#faad14',
  TIME_EXCESSIVE: '#1677ff',
  SEAL_MISMATCH: '#ff4d4f',
  SEAL_DAMAGED: '#faad14',
};

const AlertCenter: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<any>({});
  const [stats, setStats] = useState<any>(null);
  const [resolveModal, setResolveModal] = useState<{ id: number } | null>(null);
  const [resolveNotes, setResolveNotes] = useState('');

  const fetchData = async (p = page) => {
    setLoading(true);
    try {
      const params: any = { page: p, page_size: 20 };
      if (filters.alert_type) params.alert_type = filters.alert_type;
      if (filters.severity) params.severity = filters.severity;
      if (filters.status) params.status = filters.status;
      const res: any = await alertApi.list(params);
      setData(res.data.items);
      setTotal(res.data.total);
    } catch {
      message.error('预警数据加载失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res: any = await alertApi.stats(30);
      setStats(res.data);
    } catch {}
  };

  useEffect(() => { fetchData(); fetchStats(); }, []);

  const handleAcknowledge = async (id: number) => {
    try {
      await alertApi.acknowledge(id);
      message.success('已确认');
      fetchData();
      fetchStats();
    } catch (err: any) {
      message.error(err?.detail || '操作失败');
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
      fetchData();
      fetchStats();
    } catch (err: any) {
      message.error(err?.detail || '操作失败');
    }
  };

  const handleDismiss = async (id: number) => {
    try {
      await alertApi.dismiss(id);
      message.success('已忽略');
      fetchData();
      fetchStats();
    } catch (err: any) {
      message.error(err?.detail || '操作失败');
    }
  };

  const columns = [
    {
      title: '类型',
      dataIndex: 'alert_type',
      width: 120,
      render: (v: string) => <Tag color={typeColors[v]}>{typeLabels[v]}</Tag>,
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      width: 90,
      render: (v: string) => (
        <Tag color={v === 'SEVERE' ? 'red' : 'gold'} icon={v === 'SEVERE' ? <WarningOutlined /> : <AlertOutlined />}>
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
      render: (v: number) => v != null ? v.toFixed(4) : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (v: string) => {
        const m: Record<string, { color: string; text: string }> = {
          PENDING: { color: 'red', text: '待处理' },
          ACKNOWLEDGED: { color: 'gold', text: '已确认' },
          RESOLVED: { color: 'green', text: '已解决' },
          DISMISSED: { color: 'default', text: '已忽略' },
        };
        const s = m[v] || { color: 'default', text: v };
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
      render: (_: any, record: any) => (
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

  // 预警类型饼图
  const pieOption = stats
    ? {
        tooltip: { trigger: 'item' as const },
        series: [
          {
            type: 'pie',
            radius: ['40%', '70%'],
            data: Object.entries(stats.by_type || {}).map(([k, v]) => ({
              name: typeLabels[k] || k,
              value: v,
            })),
            label: { show: true, formatter: '{b}: {c}' },
          },
        ],
      }
    : null;

  return (
    <div>
      {/* 统计卡片 */}
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
                value={stats.by_status?.PENDING || 0}
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<WarningOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic
                title="已解决"
                value={stats.by_status?.RESOLVED || 0}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card size="small">
              <Statistic title="严重预警" value={stats.by_severity?.SEVERE || 0} valueStyle={{ color: '#ff4d4f' }} />
            </Card>
          </Col>
        </Row>
      )}

      {/* 筛选 + 表格 */}
      <Card>
        <Space wrap style={{ marginBottom: 16 }}>
          <Select
            placeholder="预警类型"
            allowClear
            style={{ width: 130 }}
            onChange={(v) => { setFilters((f: any) => ({ ...f, alert_type: v })); setTimeout(() => fetchData(1), 0); }}
            options={Object.entries(typeLabels).map(([k, v]) => ({ value: k, label: v }))}
          />
          <Select
            placeholder="严重程度"
            allowClear
            style={{ width: 110 }}
            onChange={(v) => { setFilters((f: any) => ({ ...f, severity: v })); setTimeout(() => fetchData(1), 0); }}
            options={[
              { value: 'GENERAL', label: '一般' },
              { value: 'SEVERE', label: '严重' },
            ]}
          />
          <Select
            placeholder="处理状态"
            allowClear
            style={{ width: 110 }}
            onChange={(v) => { setFilters((f: any) => ({ ...f, status: v })); setTimeout(() => fetchData(1), 0); }}
            options={[
              { value: 'PENDING', label: '待处理' },
              { value: 'ACKNOWLEDGED', label: '已确认' },
              { value: 'RESOLVED', label: '已解决' },
              { value: 'DISMISSED', label: '已忽略' },
            ]}
          />
        </Space>

        <Table
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
            onChange: (p) => { setPage(p); fetchData(p); },
          }}
        />
      </Card>

      {/* 处理弹窗 */}
      <Modal
        title="处理预警"
        open={!!resolveModal}
        onCancel={() => { setResolveModal(null); setResolveNotes(''); }}
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
