import { useEffect, useState } from 'react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import './LiveComponents.css';

interface LiveSparklineProps {
  data?: number[];
  color?: string;
  height?: number;
  width?: number;
  autoUpdate?: boolean;
  interval?: number;
  maxPoints?: number;
}

export default function LiveSparkline({
  data: initialData,
  color = 'var(--accent-primary)',
  height = 40,
  width = 120,
  autoUpdate = true,
  interval = 2000,
  maxPoints = 20,
}: LiveSparklineProps) {
  const [data, setData] = useState(() => 
    initialData || Array.from({ length: maxPoints }, () => Math.random() * 100)
  );

  useEffect(() => {
    if (!autoUpdate) return;

    const intervalId = setInterval(() => {
      setData(prev => {
        const newData = [...prev, Math.random() * 100 + Math.random() * 20 - 10];
        return newData.slice(-maxPoints);
      });
    }, interval);

    return () => clearInterval(intervalId);
  }, [autoUpdate, interval, maxPoints]);

  const chartData = data.map((value, index) => ({ value, index }));

  return (
    <div className="live-sparkline" style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
