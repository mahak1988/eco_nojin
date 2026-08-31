/**
 * ToolModeControls
 * =================
 * Tool mode selector + contextual UI for draw-polygon and place-op.
 *
 * @module features/hydroma/components/sidebar/ToolModeControls
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';
import { TOOL_MODES, ENGINEERING_OPS } from '../../constants';
import { usePolygonDrawing } from '../../hooks';
import { sidebarStyles } from './styles';

export function ToolModeControls() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const toolMode = useHydromaStore((s) => s.toolMode);
  const selectedOpType = useHydromaStore((s) => s.selectedOpType);
  const setToolMode = useHydromaStore((s) => s.setToolMode);
  const setSelectedOpType = useHydromaStore((s) => s.setSelectedOpType);

  const { finish, cancel, canFinish, pointCount } = usePolygonDrawing(isFa);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>{isFa ? 'حالت ابزار' : 'Tool Mode'}</div>

      {/* Main tool buttons */}
      <div style={sidebarStyles.column}>
        {TOOL_MODES.map((t) => (
          <button
            key={t.id}
            onClick={() => setToolMode(t.id)}
            style={sidebarStyles.toolButton(toolMode === t.id, t.color)}
          >
            <span style={{ fontSize: '16px' }}>{t.icon}</span>
            <span>{isFa ? t.fa : t.label}</span>
          </button>
        ))}
      </div>

      {/* Draw polygon UI */}
      {toolMode === 'draw-polygon' && (
        <div style={sidebarStyles.alertBox('#fbbf24')}>
          💡 {isFa ? 'روی زمین کلیک کنید (نقاط: ' : 'Click terrain ('}
          {pointCount})
          <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
            <button
              onClick={finish}
              disabled={!canFinish}
              style={{
                flex: 1,
                padding: '6px',
                borderRadius: '4px',
                background: canFinish ? '#f59e0b' : 'rgba(255,255,255,0.1)',
                color: 'white',
                border: 'none',
                cursor: canFinish ? 'pointer' : 'not-allowed',
                fontSize: '11px',
              }}
            >
              ✓ {isFa ? 'اتمام' : 'Finish'}
            </button>
            <button
              onClick={cancel}
              style={{
                flex: 1,
                padding: '6px',
                borderRadius: '4px',
                background: 'rgba(239, 68, 68, 0.2)',
                color: '#fca5a5',
                border: 'none',
                cursor: 'pointer',
                fontSize: '11px',
              }}
            >
              ✕ {isFa ? 'پاک' : 'Clear'}
            </button>
          </div>
        </div>
      )}

      {/* Place operation UI */}
      {toolMode === 'place-op' && (
        <div style={{ marginTop: '8px' }}>
          <div style={{ ...sidebarStyles.labelInline, marginBottom: '4px' }}>
            {isFa ? 'نوع عملیات:' : 'Operation type:'}
          </div>
          <div style={sidebarStyles.grid2}>
            {ENGINEERING_OPS.map((op) => (
              <button
                key={op.id}
                onClick={() => setSelectedOpType(op.id)}
                style={sidebarStyles.opButton(selectedOpType === op.id)}
              >
                <span style={{ fontSize: '14px' }}>{op.emoji}</span>
                <div>{isFa ? op.fa : op.name}</div>
              </button>
            ))}
          </div>
          {selectedOpType && (
            <div
              style={{
                marginTop: '6px',
                padding: '6px',
                background: 'rgba(139, 92, 246, 0.15)',
                borderRadius: '6px',
                fontSize: '11px',
                color: '#c4b5fd',
                textAlign: 'center',
              }}
            >
              ✓ {isFa ? 'روی زمین کلیک کنید' : 'Click on terrain to place'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
