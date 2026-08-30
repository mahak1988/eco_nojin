/**
 * EventDistributionChart Component
 * ===================================
 * @module features/security/components
 */

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';
import { Zap } from 'lucide-react';
import type { SecurityStats } from '../types';

interface EventDistributionChartProps {
  stats: SecurityStats;
}

export function EventDistributionChart({ stats }: EventDistributionChartProps) {
  const data = [
    { name: 'Success', value: stats.successCount, fill: '#10b981' },
    { name: 'Failed', value: stats.failedCount, fill: '#ef4444' },
    { name: 'Unique IPs', value: stats.uniqueFailedIPs, fill: '#f59e0b' },
  ];

  return (
    <div className="chart-container">
      <div className="chart-title">
        <Zap size={20} />
        Event Distribution
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
          <YAxis stroke="var(--text-muted)" fontSize={12} />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-card-solid)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
            }}
          />
          <Bar dataKey="value" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
