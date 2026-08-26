import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
  color?: 'primary' | 'accent' | 'success' | 'warning' | 'error' | 'info';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  icon,
  color = 'primary' }) => {
  const colorMap = {
    primary: 'var(--color-primary)',
    accent: 'var(--color-accent)',
    success: 'var(--color-success)',
    warning: 'var(--color-warning)',
    error: 'var(--color-error)',
    info: 'var(--color-info)' };

  const bgColor = colorMap[color];
  const isPositive = change && change > 0;

  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ flex: 1 }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-tertiary)', margin: 0 }}>
            {title}
          </p>
          <h2 style={{ fontSize: '2rem', fontWeight: 700, margin: '0.5rem 0' }}>
            {value}
          </h2>
          {change !== undefined && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem',
                fontSize: '0.875rem',
                color: isPositive ? 'var(--color-success)' : 'var(--color-error)' }}
            >
              {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
              <span>{Math.abs(change)}%</span>
            </div>
          )}
        </div>
        {icon && (
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 'var(--radius-xl)',
              background: `${bgColor}20`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: bgColor }}
          >
            {icon}
          </div>
        )}
      </div>
    </motion.div>
  );
};
