"use client";
import { motion } from 'framer-motion';
import { useTheme } from '../../lib/theme-context';
import { useI18n } from '../../lib/i18n-context';

interface Props {
  name: string; value: number; unit: string;
  min: number; max: number; optimal: [number, number];
}

export default function NutrientMeter({ name, value, unit, min, max, optimal }: Props) {
  const { colors } = useTheme();
  const { t } = useI18n();
  const range = max - min;
  const pct = Math.min(100, Math.max(0, ((value - min) / range) * 100));
  const optStart = ((optimal[0] - min) / range) * 100;
  const optWidth = ((optimal[1] - optimal[0]) / range) * 100;
  
  const isOptimal = value >= optimal[0] && value <= optimal[1];
  const isLow = value < optimal[0];
  const color = isOptimal ? colors.success : isLow ? colors.danger : colors.warm;

  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: '600', color: colors.text }}>{name}</span>
          <span style={{
            fontSize: '0.7rem', padding: '2px 8px', borderRadius: '100px',
            background: isOptimal ? `${colors.success}20` : isLow ? `${colors.danger}20` : `${colors.warm}20`,
            color: isOptimal ? colors.success : isLow ? colors.danger : colors.warm,
            fontWeight: '600',
          }}>
            {t(isOptimal ? 'soil_nutrient_optimal' : isLow ? 'soil_nutrient_low' : 'soil_nutrient_high')}
          </span>
        </div>
        <div style={{ fontWeight: '700', color }}>
          {value} <span style={{ fontSize: '0.75rem', color: colors.textMuted }}>{unit}</span>
        </div>
      </div>
      
      <div style={{ position: 'relative', height: '8px', background: colors.bg, borderRadius: '4px', overflow: 'hidden' }}>
        {/* Optimal zone */}
        <div style={{
          position: 'absolute', left: `${optStart}%`, width: `${optWidth}%`,
          height: '100%', background: `${colors.success}30`,
        }} />
        {/* Value bar */}
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{ height: '100%', background: color, borderRadius: '4px' }}
        />
      </div>
    </div>
  );
}
