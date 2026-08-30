/**
 * AuthTrendChart Component
 * =========================
 * @module features/security/components
 */

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { Activity } from 'lucide-react';
import type { HourlyData } from '../types';

interface AuthTrendChartProps {
  data: HourlyData[];
}

export function AuthTrendChart({ data }: AuthTrendChartProps) {
  return (
    <div className="chart-container">
      <div className="chart-title">
        <Activity size={20} />
        Authentication Trend (24h)
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="hour" stroke="var(--text-muted)" fontSize={11} />
          <YAxis stroke="var(--text-muted)" fontSize={11} />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-card-solid)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
            }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="success"
            stroke="#10b981"
            fillOpacity={1}
            fill="url(#colorSuccess)"
            name="Successful"
          />
          <Area
            type="monotone"
            dataKey="failed"
            stroke="#ef4444"
            fillOpacity={1}
            fill="url(#colorFailed)"
            name="Failed"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
