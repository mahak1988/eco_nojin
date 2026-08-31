import { useAnimatedCounter } from './useLiveMetrics';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import './LiveComponents.css';

interface LiveCounterProps {
  value: number;
  label: string;
  icon?: React.ReactNode;
  prefix?: string;
  suffix?: string;
  trend?: number; // percentage change
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  size?: 'sm' | 'md' | 'lg';
  decimals?: number;
}

export default function LiveCounter({
  value,
  label,
  icon,
  prefix = '',
  suffix = '',
  trend,
  color = 'primary',
  size = 'md',
  decimals = 0,
}: LiveCounterProps) {
  const animatedValue = useAnimatedCounter(value, 800);

  const colorMap = {
    primary: 'var(--accent-primary)',
    success: 'var(--accent-primary)',
    warning: 'var(--accent-secondary)',
    danger: 'var(--accent-danger)',
    info: 'var(--accent-info)',
    purple: 'var(--accent-purple)',
  };

  const sizeMap = {
    sm: { value: '24px', label: '11px' },
    md: { value: '32px', label: '12px' },
    lg: { value: '48px', label: '14px' },
  };

  const formattedValue =
    decimals > 0
      ? animatedValue.toLocaleString('en-US', { maximumFractionDigits: decimals })
      : animatedValue.toLocaleString('en-US');

  return (
    <motion.div
      className="live-counter-card"
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ type: 'spring', stiffness: 300 }}
      style={{ '--card-color': colorMap[color] } as any}
    >
      <div className="live-counter-header">
        <div className="live-counter-icon" style={{ color: colorMap[color] }}>
          {icon}
        </div>
        <div className="live-counter-label">{label}</div>
        {trend !== undefined && (
          <div
            className={`live-counter-trend ${trend > 0 ? 'positive' : trend < 0 ? 'negative' : 'neutral'}`}
          >
            {trend > 0 ? (
              <TrendingUp size={12} />
            ) : trend < 0 ? (
              <TrendingDown size={12} />
            ) : (
              <Minus size={12} />
            )}
            {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>

      <div className="live-counter-value-wrapper">
        {prefix && <span className="live-counter-prefix">{prefix}</span>}
        <motion.span
          className="live-counter-value"
          style={{ fontSize: sizeMap[size].value }}
          key={animatedValue}
          initial={{ opacity: 0.5, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {formattedValue}
        </motion.span>
        {suffix && <span className="live-counter-suffix">{suffix}</span>}
      </div>

      <div className="live-counter-indicator">
        <span className="live-dot" />
        LIVE
      </div>
    </motion.div>
  );
}
