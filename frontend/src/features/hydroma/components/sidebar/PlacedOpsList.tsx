/**
 * PlacedOpsList
 * ==============
 * List of placed engineering operations with delete.
 *
 * @module features/hydroma/components/sidebar/PlacedOpsList
 */

import { useTranslation } from 'react-i18next';
import { Trash2 } from 'lucide-react';
import { useHydromaStore } from '../../store';
import { ENGINEERING_OPS } from '../../constants';
import { sidebarStyles } from './styles';

export function PlacedOpsList() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const placedOps = useHydromaStore((s) => s.placedOps);
  const removePlacedOp = useHydromaStore((s) => s.removePlacedOp);

  if (placedOps.length === 0) return null;

  return (
    <div style={sidebarStyles.section}>
      <div style={{ fontSize: '12px', color: '#c4b5fd', marginBottom: '8px', fontWeight: 700 }}>
        📍 {isFa ? `جانمایی (${placedOps.length})` : `Placed (${placedOps.length})`}
      </div>

      {placedOps.map((op) => {
        const opDef = ENGINEERING_OPS.find((o) => o.id === op.type);
        return (
          <div
            key={op.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 8px',
              background: 'rgba(139, 92, 246, 0.1)',
              borderRadius: '6px',
              marginBottom: '4px',
              fontSize: '11px',
              border: '1px solid rgba(139, 92, 246, 0.2)',
            }}
          >
            <span>{opDef?.emoji}</span>
            <span style={{ flex: 1, color: 'white' }}>{op.label}</span>
            <span
              style={{
                color: 'rgba(255,255,255,0.4)',
                fontSize: '9px',
                fontFamily: 'monospace',
              }}
            >
              [{op.x.toFixed(1)},{op.y.toFixed(1)}]
            </span>
            <button onClick={() => removePlacedOp(op.id)} style={sidebarStyles.deleteButton}>
              <Trash2 size={11} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
