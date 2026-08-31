import { motion } from 'framer-motion';
import './LiveComponents.css';

interface LiveGaugeProps {
  value: number; // 0-100
  label: string;
  maxValue?: number;
  size?: number;
  color?: 'primary' | 'success' | 'warning' | 'danger';
  showValue?: boolean;
  unit?: string;
}

export default function LiveGauge({
  value,
  label,
  maxValue = 100,
  size = 160,
  color = 'primary',
  showValue = true,
  unit = '%',
}: LiveGaugeProps) {
  const percentage = Math.min(100, Math.max(0, (value / maxValue) * 100));
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const colorMap = {
    primary: ['#10b981', '#059669'],
    success: ['#10b981', '#34d399'],
    warning: ['#f59e0b', '#d97706'],
    danger: ['#ef4444', '#dc2626'],
  };

  const [startColor, endColor] = colorMap[color];
  const gradientId = `gauge-gradient-${label.replace(/\s/g, '')}`;

  return (
    <div className="live-gauge-container">
      <svg width={size} height={size} className="live-gauge-svg">
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={startColor} />
            <stop offset="100%" stopColor={endColor} />
          </linearGradient>
        </defs>

        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="var(--border-color)"
          strokeWidth="12"
          fill="none"
        />

        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={`url(#${gradientId})`}
          strokeWidth="12"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{
            transform: 'rotate(-90deg)',
            transformOrigin: '50% 50%',
          }}
        />
      </svg>

      {showValue && (
        <div className="live-gauge-value">
          <motion.div
            className="gauge-number"
            key={value}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
            style={{ color: startColor }}
          >
            {Math.round(value)}
          </motion.div>
          <div className="gauge-unit">{unit}</div>
        </div>
      )}

      <div className="live-gauge-label">{label}</div>
    </div>
  );
}
