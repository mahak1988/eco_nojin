/**
 * LayersPanel
 * ============
 * Terrain layer visibility toggles.
 *
 * @module features/hydroma/components/sidebar/LayersPanel
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';
import { LAYERS } from '../../constants';
import type { LayerVisibility } from '../../types';
import { sidebarStyles } from './styles';

export function LayersPanel() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const layers = useHydromaStore((s) => s.layers);
  const showNdvi = useHydromaStore((s) => s.showNdvi);
  const toggleLayer = useHydromaStore((s) => s.toggleLayer);
  const setShowNdvi = useHydromaStore((s) => s.setShowNdvi);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>{isFa ? 'لایه‌ها' : 'Layers'}</div>

      {LAYERS.map((l) => {
        const isActive =
          l.key === 'ndvi' ? showNdvi : (layers[l.key as keyof LayerVisibility] ?? false);

        const handleChange = () => {
          if (l.key === 'ndvi') {
            setShowNdvi(!showNdvi);
          } else {
            toggleLayer(l.key as keyof LayerVisibility);
          }
        };

        return (
          <label
            key={l.key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 8px',
              borderRadius: '6px',
              cursor: 'pointer',
              background: isActive ? `${l.color}20` : 'transparent',
              marginBottom: '4px',
              fontSize: '12px',
            }}
          >
            <input
              type="checkbox"
              checked={isActive}
              onChange={handleChange}
              style={{ accentColor: l.color }}
            />
            <span
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: l.color,
              }}
            />
            <span
              style={{
                color: 'white',
                fontWeight: isActive ? 700 : 500,
              }}
            >
              {isFa ? l.fa : l.label}
            </span>
          </label>
        );
      })}
    </div>
  );
}
