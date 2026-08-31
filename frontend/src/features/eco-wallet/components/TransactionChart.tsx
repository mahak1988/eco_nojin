/**
 * TransactionChart Component
 * ===========================
 * Area chart showing earnings vs redemptions over time.
 *
 * Uses deterministic data from mockData (no Math.random in render).
 *
 * @module features/eco-wallet/components
 */

import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { TrendingUp } from 'lucide-react';
import type { TransactionDataPoint } from '../types';
import { DEFAULT_TRANSACTION_HISTORY } from '../constants/mockData';
import { CHART_COLORS } from '../constants/config';

interface TransactionChartProps {
  data?: TransactionDataPoint[];
}

export function TransactionChart({ data = DEFAULT_TRANSACTION_HISTORY }: TransactionChartProps) {
  // Memoize to prevent unnecessary re-renders
  const chartData = useMemo(() => data, [data]);

  return (
    <div className="chart-container">
      <div className="chart-title">
        <TrendingUp size={20} />
        Earnings vs Redemptions (30 days)
      </div>
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="earningsGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={CHART_COLORS.earnings} stopOpacity={0.8} />
              <stop offset="95%" stopColor={CHART_COLORS.earnings} stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="redemptionsGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={CHART_COLORS.redemptions} stopOpacity={0.8} />
              <stop offset="95%" stopColor={CHART_COLORS.redemptions} stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="day" stroke="var(--text-muted)" fontSize={11} />
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
            dataKey="earnings"
            stroke={CHART_COLORS.earnings}
            fillOpacity={1}
            fill="url(#earningsGradient)"
            name="Earnings"
          />
          <Area
            type="monotone"
            dataKey="redemptions"
            stroke={CHART_COLORS.redemptions}
            fillOpacity={1}
            fill="url(#redemptionsGradient)"
            name="Redemptions"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
