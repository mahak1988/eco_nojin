import React, { useState } from 'react';
import { Layout, Menu, Breadcrumb, Button, Dropdown, Space, Avatar, Typography } from 'antd';
import {
  DashboardOutlined,
  EnvironmentOutlined,
  BarChartOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { Outlet, Link, useLocation } from 'react-router-dom';

const { Header, Content, Sider } = Layout;
const { Text } = Typography;

const AppLayout: React.FC = () => {
  const location = useLocation();
  const [currentUser, setCurrentUser] = useState<{ name: string; email: string } | null>({
    name: "کاربر تست",
    email: "test@example.com"
  });

  // Function to handle logout
  const handleLogout = () => {
    setCurrentUser(null);
    // In a real app, you would clear tokens and redirect to login
    console.log("Logged out");
  };

  // Menu items for user dropdown
  const userMenuItems = [
    {
      key: 'profile',
      label: 'پروفایل',
      icon: <UserOutlined />,
    },
    {
      key: 'logout',
      label: 'خروج',
      icon: <LogoutOutlined />,
      danger: true,
      onClick: handleLogout,
    },
  ];

  // Sidebar menu items
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: <Link to="/dashboard">داشبورد</Link>,
    },
    {
      key: '/terrain-analysis',
      icon: <EnvironmentOutlined />,
      label: <Link to="/terrain-analysis">تحلیل زمین</Link>,
    },
    {
      key: '/reports',
      icon: <BarChartOutlined />,
      label: <Link to="/reports">گزارش‌ها</Link>,
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: <Link to="/settings">تنظیمات</Link>,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible>
        <div
          style={{
            height: 32,
            margin: 16,
            background: 'rgba(255, 255, 255, 0.2)',
            borderRadius: 6,
            textAlign: 'center',
            color: '#fff',
            lineHeight: '32px',
          }}
        >
          اکو نوژین
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingRight: 24 }}>
          <Breadcrumb style={{ margin: '16px 0 16px 24' }}>
            <Breadcrumb.Item>خانه</Breadcrumb.Item>
            <Breadcrumb.Item>{location.pathname.replace('/', '') || 'داشبورد'}</Breadcrumb.Item>
          </Breadcrumb>
          
          {/* User Profile Section */}
          {currentUser && (
            <Dropdown menu={{ items: userMenuItems }} trigger={['click']}>
              <Space style={{ cursor: 'pointer' }}>
                <Avatar size="small" icon={<UserOutlined />} />
                <Text strong>{currentUser.name}</Text>
              </Space>
            </Dropdown>
          )}
        </Header>
        <Content style={{ margin: '16px' }}>
          {/* محتوای صفحات داخل Outlet قرار می‌گیرد */}
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;