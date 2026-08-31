/**
 * OrdersByStatusChart Component
 * ================================
 * @module features/marketplace/components
 */

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { ShoppingBag } from 'lucide-react';
import type { PieDataPoint } from '../types';
import { CHART_COLORS } from '../constants/config';

interface OrdersByStatusChartProps {
  pieData: PieDataPoint[];
}

export function OrdersByStatusChart({ pieData }: OrdersByStatusChartProps) {
  return (
    <div className="chart-container">
      <div className="chart-title">
        <ShoppingBag size={20} />
        Orders by Status
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
            outerRadius={90}
            fill="#8884d8"
            dataKey="value"
          >
            {pieData.map((_, index) => (
              <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: 'var(--bg-card-solid)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
