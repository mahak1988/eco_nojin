/**
 * WindControls
 * =============
 * Wind speed and direction sliders.
 *
 * @module features/hydroma/components/sidebar/WindControls
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';
import { sidebarStyles } from './styles';

export function WindControls() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const windSpeed = useHydromaStore((s) => s.climate.windSpeed);
  const windDirection = useHydromaStore((s) => s.climate.windDirection);
  const setWindSpeed = useHydromaStore((s) => s.setWindSpeed);
  const setWindDirection = useHydromaStore((s) => s.setWindDirection);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>💨 {isFa ? 'باد' : 'Wind'}</div>

      <label style={sidebarStyles.labelInline}>
        {isFa ? 'سرعت' : 'Speed'}: {windSpeed} km/h
      </label>
      <input
        type="range"
        min={0}
        max={100}
        value={windSpeed}
        onChange={(e) => setWindSpeed(parseInt(e.target.value))}
        style={{ width: '100%', accentColor: '#a855f7' }}
      />

      <label style={{ ...sidebarStyles.labelInline, marginTop: '8px' }}>
        {isFa ? 'جهت' : 'Direction'}: {windDirection}°
      </label>
      <input
        type="range"
        min={0}
        max={360}
        value={windDirection}
        onChange={(e) => setWindDirection(parseInt(e.target.value))}
        style={{ width: '100%', accentColor: '#a855f7' }}
      />
    </div>
  );
}
