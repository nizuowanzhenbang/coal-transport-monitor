import React from 'react';
import { Card, Descriptions, Typography, Alert, Tag } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

const Settings: React.FC = () => {
  return (
    <div>
      <Card title="系统设置" style={{ marginBottom: 16 }}>
        <Alert
          message="风险预警阈值配置"
          description="以下为系统当前使用的预警判定规则，修改需联系管理员调整后端配置。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="重量固定阈值">3‰（千分之三）</Descriptions.Item>
          <Descriptions.Item label="亏吨判定">进厂净重低于出港净重，偏差 &gt; 3‰</Descriptions.Item>
          <Descriptions.Item label="盈吨判定">进厂净重高于出港净重，偏差 &gt; 3‰</Descriptions.Item>
          <Descriptions.Item label="重量动态阈值">Z-score 2σ(一般) / 3σ(严重)</Descriptions.Item>
          <Descriptions.Item label="时间一般预警">运输时长 &gt; 正常基准 + 30分钟</Descriptions.Item>
          <Descriptions.Item label="时间严重预警">运输时长 &gt; 正常基准 + 60分钟</Descriptions.Item>
          <Descriptions.Item label="时间基准计算">历史中位数 + IQR去极值</Descriptions.Item>
          <Descriptions.Item label="铅封不一致">出港/进厂二维码不匹配 → 严重预警</Descriptions.Item>
          <Descriptions.Item label="铅封损坏">二维码无法识别/损坏 → 一般预警</Descriptions.Item>
          <Descriptions.Item label="历史数据窗口">最近100条运输记录</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="风险评分规则" style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered size="small">
          <Descriptions.Item label="评分公式">Σ(预警类型权重 × 严重程度系数)</Descriptions.Item>
          <Descriptions.Item label="重量异常权重">0.4</Descriptions.Item>
          <Descriptions.Item label="时间异常权重">0.3</Descriptions.Item>
          <Descriptions.Item label="铅封异常权重">0.3</Descriptions.Item>
          <Descriptions.Item label="一般预警系数">1.0</Descriptions.Item>
          <Descriptions.Item label="严重预警系数">2.0</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="参考标准">
        <Paragraph>
          <InfoCircleOutlined style={{ marginRight: 8 }} />
          本系统依据 <Text strong>DL/T 1668-2016《火电厂燃煤管理技术导则》</Text> 设计
        </Paragraph>
        <Paragraph type="secondary">
          4.1.1 燃煤装载过程宜采用实时视频、网络视频和车厢封条等技术手段进行监督。
          监装记录应详细记录和保存以下信息：装载时间、装载地点、装载工具、装载方式、
          运输工具、装载量、有无掺混、天气状况、异常情况、监装人员。
        </Paragraph>
      </Card>
    </div>
  );
};

export default Settings;
