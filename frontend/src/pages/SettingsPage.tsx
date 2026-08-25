import React from 'react';
import { Typography, Card } from 'antd';

const Settings: React.FC = () => {
  return (
    <Card>
      <Typography.Title level={3}>تنظیمات</Typography.Title>
      <Typography.Paragraph>
        این بخش برای تنظیمات برنامه در نظر گرفته شده است.
      </Typography.Paragraph>
    </Card>
  );
};

export default Settings;