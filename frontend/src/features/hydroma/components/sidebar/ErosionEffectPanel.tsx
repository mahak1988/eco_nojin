/**
 * ErosionEffectPanel
 * ===================
 * Displays RUSLE erosion calculation results.
 *
 * @module features/hydroma/components/sidebar/ErosionEffectPanel
 */

import { TrendingUp } from 'lucide-react';
import { useHydromaStore } from '../../store';

export function ErosionEffectPanel() {
  const erosionEffect = useHydromaStore((s) => s.erosionEffect);

  if (!erosionEffect) return null;

  return (
    <div
      style={{
        background: 'rgba(76,175,80,0.12)',
        borderRadius: '12px',
        padding: '12px',
        border: '1px solid rgba(76,175,80,0.3)',
        fontSize: '11.5px',
        color: '#dcefe0',
      }}
    >
      <div
        style={{
          fontWeight: 700,
          marginBottom: 6,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <TrendingUp size={13} color="#4CAF50" /> اثر {erosionEffect.op_fa} — RUSLE واقعی
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>فرسایش قبل:</span>
        <b dir="ltr">{erosionEffect.A_before_t_ha_yr} t/ha/yr</b>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>فرسایش بعد:</span>
        <b style={{ color: '#81C784' }} dir="ltr">
          {erosionEffect.A_after_t_ha_yr} t/ha/yr
        </b>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>کاهش:</span>
        <b style={{ color: '#4CAF50' }}>{erosionEffect.reduction_pct}٪</b>
      </div>

      <div style={{ marginTop: 6, color: '#B0BEC5' }}>{erosionEffect.note_fa}</div>
    </div>
  );
}
