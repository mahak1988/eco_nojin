/**
 * VisualControls
 * ================
 * Decor, growth, crop, and plots management.
 *
 * @module features/hydroma/components/sidebar/VisualControls
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';
import { sidebarStyles } from './styles';

export function VisualControls() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const visual = useHydromaStore((s) => s.visual);
  const plots = useHydromaStore((s) => s.plots);

  const setShowDecor = useHydromaStore((s) => s.setShowDecor);
  const setGrowth = useHydromaStore((s) => s.setGrowth);
  const setCropVisual = useHydromaStore((s) => s.setCropVisual);
  const clearPlots = useHydromaStore((s) => s.clearPlots);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>
        {isFa ? 'نمایش و داده' : 'Visual & Data'}
      </div>

      {/* Decor toggle */}
      <label
        style={{
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
          fontSize: '12px',
          color: 'white',
          marginBottom: '6px',
        }}
      >
        <input
          type="checkbox"
          checked={visual.showDecor}
          onChange={(e) => setShowDecor(e.target.checked)}
        />
        🏡 {isFa ? 'گرافیک مزرعه' : 'Farm decor'}
      </label>

      {/* Growth slider */}
      <label style={sidebarStyles.labelInline}>
        {isFa ? 'رشد' : 'Growth'}: {Math.round(visual.growth * 100)}%
      </label>
      <input
        type="range"
        min={0}
        max={1}
        step={0.05}
        value={visual.growth}
        onChange={(e) => setGrowth(parseFloat(e.target.value))}
        style={{
          width: '100%',
          accentColor: '#2f9e44',
          marginBottom: '8px',
        }}
      />

      {/* Crop selector */}
      <select
        value={visual.cropVisual}
        onChange={(e) => setCropVisual(e.target.value as 'corn' | 'wheat' | 'alfalfa')}
        style={{
          width: '100%',
          padding: '6px',
          borderRadius: 6,
          background: '#1e293b',
          color: 'white',
          border: '1px solid rgba(255,255,255,0.2)',
          marginBottom: '8px',
        }}
      >
        <option value="corn">🌽 {isFa ? 'ذرت' : 'Corn'}</option>
        <option value="wheat">🌾 {isFa ? 'گندم' : 'Wheat'}</option>
        <option value="alfalfa">🌿 {isFa ? 'یونجه' : 'Alfalfa'}</option>
      </select>

      {/* Plots display */}
      <div style={{ ...sidebarStyles.labelInline, marginBottom: '6px' }}>
        {isFa ? `پلات‌های داده: ${plots.length}` : `Data plots: ${plots.length}`}
      </div>

      {plots.slice(-4).reverse().map((p) => (
        <div
          key={p.id}
          style={{
            background: 'rgba(57,255,90,0.08)',
            border: '1px solid rgba(57,255,90,0.3)',
            borderRadius: 8,
            padding: '6px 8px',
            marginBottom: 6,
            fontSize: 10,
            color: 'white',
          }}
        >
          💧 {Math.round(p.data.moisture * 100)}% • 🌿{' '}
          {p.data.ndvi.toFixed(2)} • 📐 {Math.round(p.data.elevation)}m
        </div>
      ))}

      {plots.length > 0 && (
        <button
          onClick={clearPlots}
          style={{
            width: '100%',
            padding: '6px',
            borderRadius: 6,
            border: 'none',
            background: 'rgba(239,68,68,0.2)',
            color: '#fca5a5',
            fontSize: 11,
            cursor: 'pointer',
          }}
        >
          🗑️ {isFa ? 'پاک کردن پلات‌ها' : 'Clear plots'}
        </button>
      )}
    </div>
  );
}
