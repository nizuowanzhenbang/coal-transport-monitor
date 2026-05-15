import React, { useEffect, useState } from 'react';
import { Layout, Menu, Button, Space, Typography, Badge } from 'antd';
import {
  DashboardOutlined,
  CarOutlined,
  AlertOutlined,
  UnorderedListOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '../stores/auth';
import { useAlertWebSocket } from '../hooks/useAlertWebSocket';
import { dashboardApi } from '../api';
import { theme } from 'antd';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

const ROLE_LABELS: Record<string, string> = {
  ADMIN: '管理员',
  OPERATOR: '操作员',
  VIEWER: '查看者',
};

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { username, role, logout, token } = useAuthStore();
  const { token: themeToken } = theme.useToken();
  const [pendingCount, setPendingCount] = useState(0);

  // 初始化待处理预警数量
  useEffect(() => {
    dashboardApi
      .overview()
      .then((res) => setPendingCount(res.data.pending_alerts))
      .catch(() => {});
  }, []);

  // WebSocket 实时更新徽标
  useAlertWebSocket({
    token,
    enabled: true,
    onNewAlert: () => {
      setPendingCount((c) => c + 1);
    },
  });

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: '监控仪表盘' },
    { key: '/transports', icon: <UnorderedListOutlined />, label: '运输记录' },
    {
      key: '/alerts',
      icon: <AlertOutlined />,
      label: (
        <Badge count={pendingCount} overflowCount={99} offset={[4, 0]} size="small">
          <span style={{ color: 'inherit' }}>预警中心</span>
        </Badge>
      ),
    },
    { key: '/vehicles', icon: <CarOutlined />, label: '车辆管理' },
    { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="dark"
        width={220}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <Title level={4} style={{ color: '#fff', margin: 0, fontSize: 14 }}>
            汽车运煤智能监督
          </Title>
          <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, marginTop: 4 }}>
            风险预警系统 v2.0
          </div>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      <Layout style={{ marginLeft: 220 }}>
        <Header
          style={{
            background: themeToken.colorBgContainer,
            padding: '0 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
            position: 'sticky',
            top: 0,
            zIndex: 10,
          }}
        >
          <div />
          <Space>
            <UserOutlined />
            <span>{username}</span>
            <span style={{ color: '#999', fontSize: 12 }}>
              ({ROLE_LABELS[role ?? ''] ?? role})
            </span>
            <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout}>
              退出
            </Button>
          </Space>
        </Header>

        <Content style={{ margin: 24, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
