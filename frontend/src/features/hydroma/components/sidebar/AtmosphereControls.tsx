/**
 * AtmosphereControls
 * ===================
 * Rain and Camera Tour toggles.
 *
 * @module features/hydroma/components/sidebar/AtmosphereControls
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';
import { sidebarStyles } from './styles';

export function AtmosphereControls() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const rainOn = useHydromaStore((s) => s.climate.rainOn);
  const tourOn = useHydromaStore((s) => s.tourOn);
  const toggleRain = useHydromaStore((s) => s.toggleRain);
  const toggleTour = useHydromaStore((s) => s.toggleTour);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>{isFa ? 'اقلیم و دوربین' : 'Atmosphere & Camera'}</div>
      <div style={sidebarStyles.grid2}>
        <button onClick={toggleRain} style={sidebarStyles.button(rainOn, '#0284c7')}>
          {isFa ? 'باران' : 'Rain'}
        </button>
        <button onClick={toggleTour} style={sidebarStyles.button(tourOn, '#7c3aed')}>
          {isFa ? 'تور دوربین' : 'Camera Tour'}
        </button>
      </div>
    </div>
  );
}
