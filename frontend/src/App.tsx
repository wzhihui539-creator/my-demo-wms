import React from 'react';
import { Layout, Menu, theme } from 'antd';
import {
  DashboardOutlined,
  InboxOutlined,
  ExportOutlined,
  StockOutlined,
  SearchOutlined,
  AlertOutlined,
  BarChartOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/inbound', icon: <InboxOutlined />, label: '入库管理' },
  { key: '/outbound', icon: <ExportOutlined />, label: '出库管理' },
  { key: '/inventory', icon: <StockOutlined />, label: '库存管理' },
  { key: '/check', icon: <SearchOutlined />, label: '盘点管理' },
  { key: '/alerts', icon: <AlertOutlined />, label: '预警管理' },
  { key: '/reports', icon: <BarChartOutlined />, label: '报表统计' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
];

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible theme="dark">
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 18, fontWeight: 'bold' }}>
          WMS系统
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: colorBgContainer, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0 }}>仓库管理系统</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span><UserOutlined /> {user?.username || '管理员'}</span>
            <a onClick={logout} style={{ cursor: 'pointer' }}><LogoutOutlined /> 退出</a>
          </div>
        </Header>
        <Content style={{ margin: 24, padding: 24, background: colorBgContainer, borderRadius: borderRadiusLG, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;