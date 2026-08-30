/**
 * PolygonsList
 * =============
 * List of drawn polygons with area and delete.
 *
 * @module features/hydroma/components/sidebar/PolygonsList
 */

import { useTranslation } from 'react-i18next';
import { Trash2, Square } from 'lucide-react';
import { useHydromaStore } from '../../store';
import { sidebarStyles } from './styles';

export function PolygonsList() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const polygons = useHydromaStore((s) => s.polygons);
  const removePolygon = useHydromaStore((s) => s.removePolygon);

  if (polygons.length === 0) return null;

  return (
    <div style={sidebarStyles.section}>
      <div style={{ fontSize: '12px', color: '#86efac', marginBottom: '8px', fontWeight: 700 }}>
        📐 {isFa ? `محدوده‌ها (${polygons.length})` : `Polygons (${polygons.length})`}
      </div>

      {polygons.map((poly) => (
        <div key={poly.id} style={sidebarStyles.listItem(poly.color)}>
          <Square size={12} style={{ color: poly.color }} />
          <span style={{ flex: 1, color: 'white' }}>{poly.name}</span>
          <span style={{ color: 'rgba(255,255,255,0.5)' }}>
            {poly.points.length} pts • {poly.area?.toFixed(0) || 0}m²
          </span>
          <button
            onClick={() => removePolygon(poly.id)}
            style={sidebarStyles.deleteButton}
          >
            <Trash2 size={11} />
          </button>
        </div>
      ))}
    </div>
  );
}
