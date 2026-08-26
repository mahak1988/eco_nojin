import React, { useState, useEffect } from 'react';
import { Card, Typography, Select, DatePicker } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

const { Title } = Typography;
const { RangePicker } = DatePicker;

// Mock data - in a real app, this would come from an API
const generateMockData = (reportType: string) => {
  if (reportType === 'users') {
    return [
      { name: 'فروردین', value: 4000 },
      { name: 'اردیبهشت', value: 3000 },
      { name: 'خرداد', value: 2000 },
      { name: 'تیر', value: 2780 },
      { name: 'مرداد', value: 1890 },
      { name: 'شهریور', value: 2390 },
    ];
  } else if (reportType === 'revenue') {
    return [
      { name: 'فروردین', uv: 4000, pv: 2400 },
      { name: 'اردیبهشت', uv: 3000, pv: 1398 },
      { name: 'خرداد', uv: 2000, pv: 9800 },
      { name: 'تیر', uv: 2780, pv: 3908 },
      { name: 'مرداد', uv: 1890, pv: 4800 },
      { name: 'شهریور', uv: 2390, pv: 3800 },
    ];
  }
  return [];
};

const Reports: React.FC = () => {
  const [reportType, setReportType] = useState<string>('users');
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // In a real app, this would be an actual API call:
        // const response = await api.get(`/reports/${reportType}`);
        // setChartData(response.data);
        
        // For now, use mock data
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
        setChartData(generateMockData(reportType));
        setLoading(false);
      } catch (error) {
        console.error(`Error fetching ${reportType} report:`, error);
        setLoading(false);
      }
    };

    fetchData();
  }, [reportType]);

  return (
    <div>
      <Title level={2}>گزارش‌ها</Title>
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Select
            defaultValue="users"
            style={{ width: 200 }}
            onChange={(value) => {
              setReportType(value);
              setLoading(true); // Reset loading state when changing report type
            }}
            options={[
              { value: 'users', label: 'گزارش کاربران' },
              { value: 'revenue', label: 'گزارش درآمد' },
            ]}
          />
          <RangePicker />
        </div>
      </Card>

      <Card loading={loading}>
        {reportType === 'users' ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={chartData}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart
              data={chartData}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="uv" stroke="#8884d8" activeDot={{ r: 8 }} />
              <Line type="monotone" dataKey="pv" stroke="#82ca9d" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </Card>
    </div>
  );
};

export default Reports;