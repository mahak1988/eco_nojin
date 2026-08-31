import React from 'react';
import { motion } from 'framer-motion';
import { Leaf, Droplets, Wind, Coins, TrendingUp } from 'lucide-react';

interface VLLResultsBarProps {
  results: any;
  isSimulating: boolean;
}

export const VLLResultsBar: React.FC<VLLResultsBarProps> = ({ results, isSimulating }) => {
  if (isSimulating) {
    return (
      <div
        style={{
          padding: '1.5rem',
          background: 'linear-gradient(90deg, var(--color-primary), var(--color-info))',
          color: 'white',
          textAlign: 'center',
        }}
      >
        <motion.div
          animate={{ opacity: [1, 0.5, 1] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          ⏳ در حال اجرای شبیه‌سازی با مدل‌های علمی (AquaCrop, RothC, RUSLE, WEPS)...
        </motion.div>
      </div>
    );
  }

  if (!results) {
    return (
      <div
        style={{
          padding: '1rem',
          background: 'var(--color-surface)',
          borderTop: '1px solid var(--color-border)',
          textAlign: 'center',
          color: 'var(--color-text-tertiary)',
        }}
      >
        💡 مداخلات را انتخاب و دکمه "اجرای سناریو" را بزنید تا نتایج شبیه‌سازی را ببینید
      </div>
    );
  }

  const score = results.sustainability_score || 0;
  const breakdown = results.score_breakdown || {};
  const scoreColor = score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444';

  const metrics = [
    { icon: <Leaf size={20} />, label: 'کربن', value: breakdown.carbon || 0, color: '#22c55e' },
    { icon: <Droplets size={20} />, label: 'آب', value: breakdown.water || 0, color: '#3b82f6' },
    { icon: <Wind size={20} />, label: 'فرسایش', value: breakdown.erosion || 0, color: '#f59e0b' },
    { icon: <Coins size={20} />, label: 'اقتصاد', value: 70, color: '#8b5cf6' },
    { icon: <TrendingUp size={20} />, label: 'پایداری', value: score, color: scoreColor },
  ];

  return (
    <div
      style={{
        padding: '1rem 2rem',
        background: 'var(--color-surface)',
        borderTop: '2px solid var(--color-border)',
        display: 'flex',
        gap: '2rem',
        alignItems: 'center',
        boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.05)',
      }}
    >
      {/* Main Score */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', minWidth: 200 }}>
        <div style={{ position: 'relative', width: 80, height: 80 }}>
          <svg width="80" height="80" style={{ transform: 'rotate(-90deg)' }}>
            <circle
              cx="40"
              cy="40"
              r="35"
              fill="none"
              stroke="var(--color-border)"
              strokeWidth="6"
            />
            <motion.circle
              cx="40"
              cy="40"
              r="35"
              fill="none"
              stroke={scoreColor}
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={220}
              initial={{ strokeDashoffset: 220 }}
              animate={{ strokeDashoffset: 220 - (score / 100) * 220 }}
              transition={{ duration: 1, ease: 'easeOut' }}
            />
          </svg>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.5rem',
              fontWeight: 700,
              color: scoreColor,
            }}
          >
            {score}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
            نمره پایداری
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 700 }}>
            {score >= 75 ? '✅ عالی' : score >= 50 ? '⚠️ متوسط' : '❌ ضعیف'}
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div
        style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem' }}
      >
        {metrics.slice(0, 4).map((metric, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            style={{
              padding: '0.75rem',
              background: `${metric.color}10`,
              border: `1px solid ${metric.color}40`,
              borderRadius: 'var(--radius-lg)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <div style={{ color: metric.color }}>{metric.icon}</div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                {metric.label}
              </div>
              <div style={{ fontSize: '1.125rem', fontWeight: 700 }}>
                {Math.round(metric.value)}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
