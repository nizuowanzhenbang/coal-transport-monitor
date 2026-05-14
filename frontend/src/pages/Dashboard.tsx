import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Spin, theme } from 'antd';
import {
  AlertOutlined,
  CarOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { dashboardApi } from '../api';
import dayjs from 'dayjs';

interface Overview {
  total_transports: number;
  today_transports: number;
  pending_alerts: number;
  severe_alerts: number;
  anomaly_rate: number;
  avg_duration_minutes: number;
  total_vehicles: number;
  active_vehicles: number;
}

interface AlertTrendItem {
  date: string;
  total: number;
  weight_count: number;
  time_count: number;
  seal_count: number;
}

interface TopRiskVehicle {
  plate_number: string;
  total_alerts: number;
  severe_count: number;
  last_alert_time: string | null;
}

interface WeightDistItem {
  range_min: number;
  range_max: number;
  count: number;
}

const Dashboard: React.FC = () => {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [trend, setTrend] = useState<AlertTrendItem[]>([]);
  const [topVehicles, setTopVehicles] = useState<TopRiskVehicle[]>([]);
  const [weightDist, setWeightDist] = useState<WeightDistItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ov, tr, tv, wd] = await Promise.all([
          dashboardApi.overview(),
          dashboardApi.alertTrend(30),
          dashboardApi.topRiskVehicles(10),
          dashboardApi.weightDistribution(12),
        ]);
        setOverview((ov as any).data);
        setTrend((tr as any).data);
        setTopVehicles((tv as any).data);
        setWeightDist((wd as any).data);
      } catch (err) {
        console.error('仪表盘数据加载失败', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  // 预警趋势图配置
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

  // 重量分布图配置
  const distOption = {
    tooltip: {
      trigger: 'axis' as const,
      formatter: (params: any) => {
        const p = params[0];
        const d = weightDist[p.dataIndex];
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
          color: (params: any) => {
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

  // 高风险车辆表格列
  const vehicleColumns = [
    {
      title: '车牌号',
      dataIndex: 'plate_number',
      render: (v: string, _: any, idx: number) => (
        <span>
          {idx < 3 && <WarningOutlined style={{ color: '#ff4d4f', marginRight: 4 }} />}
          {v}
        </span>
      ),
    },
    { title: '预警总数', dataIndex: 'total_alerts', sorter: (a: any, b: any) => a.total_alerts - b.total_alerts },
    {
      title: '严重预警',
      dataIndex: 'severe_count',
      render: (v: number) => (v > 0 ? <Tag color="red">{v}</Tag> : <Tag color="green">0</Tag>),
    },
    {
      title: '最近预警',
      dataIndex: 'last_alert_time',
      render: (v: string) => (v ? dayjs(v).format('MM-DD HH:mm') : '-'),
    },
  ];

  return (
    <div>
      {/* KPI卡片 */}
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
              value={((overview?.anomaly_rate || 0) * 100).toFixed(1)}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: (overview?.anomaly_rate || 0) > 0.1 ? '#ff4d4f' : '#52c41a' }}
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

      {/* 图表区域 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={14}>
          <Card title="预警趋势（近30天）">
            <ReactECharts option={trendOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="重量偏差分布">
            <ReactECharts option={distOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      {/* 高风险车辆 */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="高风险车辆 TOP10">
            <Table
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
