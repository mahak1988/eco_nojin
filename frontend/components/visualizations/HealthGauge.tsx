"use client";
import { motion } from 'framer-motion';
import { useTheme } from '../../lib/theme-context';

interface Props { score: number; label?: string; }

export default function HealthGauge({ score, label = 'Soil Health' }: Props) {
  const { colors } = useTheme();
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  
  const color = score >= 70 ? colors.success : score >= 40 ? colors.warm : colors.danger;
  const status = score >= 70 ? 'Excellent' : score >= 40 ? 'Moderate' : 'Poor';

  return (
    <div style={{ textAlign: 'center' }}>
      <svg width="200" height="200" viewBox="0 0 200 200">
        {/* Background circle */}
        <circle cx="100" cy="100" r={radius} fill="none"
          stroke={colors.border} strokeWidth="14" opacity="0.3" />
        
        {/* Progress arc */}
        <motion.circle
          cx="100" cy="100" r={radius} fill="none"
          stroke={color} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference - progress }}
          transition={{ duration: 1.5, ease: 'easeOut' }}
          transform="rotate(-90 100 100)"
        />
        
        {/* Score text */}
        <text x="100" y="95" textAnchor="middle" fill={colors.text}
          fontSize="42" fontWeight="800">{score}</text>
        <text x="100" y="120" textAnchor="middle" fill={colors.textMuted}
          fontSize="14">/100</text>
      </svg>
      <div style={{ marginTop: '8px' }}>
        <div style={{ fontSize: '0.9rem', color: colors.textMuted }}>{label}</div>
        <div style={{ fontSize: '1.1rem', fontWeight: '700', color, marginTop: '4px' }}>
          {status}
        </div>
      </div>
    </div>
  );
}
