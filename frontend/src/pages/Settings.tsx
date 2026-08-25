import React from 'react';
import { Typography, Card, Switch, Space } from 'antd';

const { Title, Text } = Typography;

const Settings: React.FC = () => {
  return (
    <div>
      <Title level={2}>تنظیمات</Title>
      <Card title="تنظیمات عمومی">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text>حالت تاریک</Text>
            <Switch defaultChecked={false} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text>اعلان‌های صوتی</Text>
            <Switch defaultChecked={true} />
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default Settings;