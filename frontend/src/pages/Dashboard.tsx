import React, { useState, useEffect } from 'react';
import { Card, Col, Row, Statistic, Button, Space, Typography, Divider } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import api from '../services/api'; // Import the API service
import useStore from '../store/useStore'; // Import the global store

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  // Access state and actions from the store
  const { count, increment, decrement, reset } = useStore();

  // Simulate fetching data from an API
  useEffect(() => {
    const fetchData = async () => {
      try {
        // In a real app, this would be an actual API call:
        // const response = await api.get('/dashboard/stats');
        // setStats(response.data);
        
        // For now, simulate data
        await new Promise(resolve => setTimeout(resolve, 1000));
        setStats({
          totalUsers: 1234,
          activeProjects: 12,
          revenue: 23567,
          growthRate: 12.3 });
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div>
      <Title level={2}>داشبورد</Title>
      <Divider />
      
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card loading={loading}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="کاربران کل"
                value={stats?.totalUsers || 0}
                precision={0}
                valueStyle={{ color: '#3f8600' }}
                prefix={<ArrowUpOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="پروژه‌های فعال"
                value={stats?.activeProjects || 0}
                precision={0}
                valueStyle={{ color: '#cf1322' }}
                prefix={<ArrowDownOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="درآمد"
                prefix={'$'}
                value={stats?.revenue || 0}
                precision={2}
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="نرخ رشد"
                value={stats?.growthRate || 0}
                precision={2}
                valueStyle={{ color: '#3f8600' }}
                suffix="%"
              />
            </Col>
          </Row>
        </Card>

        <Card title="تست Zustand Store">
          <p>Count: {count}</p>
          <Space>
            <Button onClick={increment}>افزایش</Button>
            <Button onClick={decrement}>کاهش</Button>
            <Button onClick={reset} danger>ریست</Button>
          </Space>
        </Card>
      </Space>
    </div>
  );
};

export default Dashboard;