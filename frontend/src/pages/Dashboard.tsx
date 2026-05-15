import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Spin, Button, notification } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  AlertOutlined,
  CarOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  ThunderboltOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { dashboardApi } from '../api';
import { useAlertWebSocket } from '../hooks/useAlertWebSocket';
import { useAuthStore } from '../stores/auth';
import type { OverviewData, AlertTrendItem, TopRiskVehicle, WeightDistItem } from '../types';
import dayjs from 'dayjs';

const REFRESH_INTERVAL_MS = 60_000;

const Dashboard: React.FC = () => {
  const { token } = useAuthStore();
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [trend, setTrend] = useState<AlertTrendItem[]>([]);
  const [topVehicles, setTopVehicles] = useState<TopRiskVehicle[]>([]);
  const [weightDist, setWeightDist] = useState<WeightDistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async (showSpinner = false) => {
    if (showSpinner) setLoading(true);
    try {
      const [ov, tr, tv, wd] = await Promise.all([
        dashboardApi.overview(),
        dashboardApi.alertTrend(30),
        dashboardApi.topRiskVehicles(10),
        dashboardApi.weightDistribution(12),
      ]);
      setOverview(ov.data);
      setTrend(tr.data);
      setTopVehicles(tv.data);
      setWeightDist(wd.data);
    } catch {
      // 静默失败，保留旧数据
    } finally {
      if (showSpinner) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(true);
  }, [fetchData]);

  // 每 60 秒自动刷新
  useEffect(() => {
    timerRef.current = setInterval(() => fetchData(false), REFRESH_INTERVAL_MS);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchData]);

  // WebSocket 实时预警通知
  useAlertWebSocket({
    token,
    enabled: true,
    onNewAlert: (msg) => {
      notification.warning({
        message: `新预警：${msg.data.severity === 'SEVERE' ? '严重' : '一般'}`,
        description: msg.data.description,
        duration: 6,
      });
      dashboardApi.overview().then((res) => setOverview(res.data)).catch(() => {});
    },
  });

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const trendOption = {
    tooltip: { trigger: 'axis' as const },
    legend: { data: ['重量异常', '时间异常', '铅封异常'], bottom: 0 },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category' as const,
      data: trend.map((t) => t.date),
      axisLabel: { formatter: (v: string) => v.slice(5) },
    },
    yAxis: { type: 'value' as const, minInterval: 1 },
    series: [
      { name: '重量异常', type: 'bar', stack: 'total', data: trend.map((t) => t.weight_count), color: '#ff4d4f' },
      { name: '时间异常', type: 'bar', stack: 'total', data: trend.map((t) => t.time_count), color: '#faad14' },
      { name: '铅封异常', type: 'bar', stack: 'total', data: trend.map((t) => t.seal_count), color: '#1677ff' },
    ],
  };

  const distOption = {
    tooltip: {
      trigger: 'axis' as const,
      formatter: (params: { dataIndex: number }[]) => {
        const d = weightDist[params[0].dataIndex];
        return `${(d.range_min * 1000).toFixed(1)}‰ ~ ${(d.range_max * 1000).toFixed(1)}‰<br/>数量: ${d.count}`;
      },
    },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category' as const,
      data: weightDist.map((d) => `${(d.range_min * 1000).toFixed(1)}‰`),
      axisLabel: { rotate: 45, fontSize: 10 },
    },
    yAxis: { type: 'value' as const, minInterval: 1 },
    series: [
      {
        type: 'bar',
        data: weightDist.map((d) => d.count),
        itemStyle: {
          color: (params: { dataIndex: number }) => {
            const mid = weightDist[params.dataIndex];
            const avg = (mid.range_min + mid.range_max) / 2;
            if (Math.abs(avg) > 0.003) return '#ff4d4f';
            if (Math.abs(avg) > 0.002) return '#faad14';
            return '#52c41a';
          },
        },
      },
    ],
  };

  const vehicleColumns: ColumnsType<TopRiskVehicle> = [
    {
      title: '车牌号',
      dataIndex: 'plate_number',
      render: (v: string, _record, idx) => (
        <span>
          {idx < 3 && <WarningOutlined style={{ color: '#ff4d4f', marginRight: 4 }} />}
          {v}
        </span>
      ),
    },
    {
      title: '预警总数',
      dataIndex: 'total_alerts',
      sorter: (a, b) => a.total_alerts - b.total_alerts,
    },
    {
      title: '严重预警',
      dataIndex: 'severe_count',
      render: (v: number) => (v > 0 ? <Tag color="red">{v}</Tag> : <Tag color="green">0</Tag>),
    },
    {
      title: '最近预警',
      dataIndex: 'last_alert_time',
      render: (v: string | null) => (v ? dayjs(v).format('MM-DD HH:mm') : '-'),
    },
  ];

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title="总运输次数"
              value={overview?.total_transports}
              prefix={<CarOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
            <div style={{ color: '#999', fontSize: 12 }}>今日 {overview?.today_transports} 次</div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title="待处理预警"
              value={overview?.pending_alerts}
              prefix={<AlertOutlined />}
              valueStyle={{ color: overview?.pending_alerts ? '#ff4d4f' : '#52c41a' }}
            />
            <div style={{ color: '#999', fontSize: 12 }}>
              严重预警 <span style={{ color: '#ff4d4f' }}>{overview?.severe_alerts}</span> 条
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title="异常率"
              value={((overview?.anomaly_rate ?? 0) * 100).toFixed(1)}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: (overview?.anomaly_rate ?? 0) > 0.1 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable>
            <Statistic
              title="平均运输时长"
              value={overview?.avg_duration_minutes}
              suffix="分钟"
              prefix={<ClockCircleOutlined />}
            />
            <div style={{ color: '#999', fontSize: 12 }}>
              在册车辆 {overview?.total_vehicles} / 活跃 {overview?.active_vehicles}
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={14}>
          <Card
            title="预警趋势（近30天）"
            extra={
              <Button size="small" icon={<ReloadOutlined />} onClick={() => fetchData(false)}>
                刷新
              </Button>
            }
          >
            <ReactECharts option={trendOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="重量偏差分布">
            <ReactECharts option={distOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="高风险车辆 TOP10">
            <Table<TopRiskVehicle>
              dataSource={topVehicles}
              columns={vehicleColumns}
              rowKey="plate_number"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
