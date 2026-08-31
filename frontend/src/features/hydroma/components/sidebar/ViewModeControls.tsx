/**
 * ViewModeControls
 * =================
 * Camera view preset selector (3D, Top, Side, Section).
 *
 * @module features/hydroma/components/sidebar/ViewModeControls
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore, selectViewMode } from '../../store';
import { VIEW_MODES } from '../../constants';
import { sidebarStyles } from './styles';

export function ViewModeControls() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';
  const viewMode = useHydromaStore(selectViewMode);
  const setViewMode = useHydromaStore((s) => s.setViewMode);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>{isFa ? 'حالت نمایش' : 'View Mode'}</div>
      <div style={sidebarStyles.grid4}>
        {VIEW_MODES.map((v) => (
          <button
            key={v.id}
            onClick={() => setViewMode(v.id)}
            style={sidebarStyles.button(viewMode === v.id)}
          >
            {isFa ? v.fa : v.label}
          </button>
        ))}
      </div>
    </div>
  );
}
