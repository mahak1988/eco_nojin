/**
 * ViewportInfoBar
 * =================
 * Top information bar for 3D viewport showing status and controls.
 *
 * @module features/hydroma/components/viewport/ViewportInfoBar
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';

export function ViewportInfoBar() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const toolMode = useHydromaStore((s) => s.toolMode);
  const lastClickInfo = useHydromaStore((s) => s.lastClickInfo);

  const statusText =
    toolMode === 'orbit'
      ? isFa
        ? '🖱️ چرخش آزاد'
        : '🖱️ Free orbit'
      : toolMode === 'draw-polygon'
        ? isFa
          ? '📐 حالت ترسیم'
          : '📐 Draw mode'
        : toolMode === 'place-op'
          ? isFa
            ? '📍 حالت جانمایی'
            : '📍 Place mode'
          : isFa
            ? '📊 پلات داده'
            : '📊 Data plot';

  return (
    <div
      style={{
        padding: '10px 16px',
        background: 'rgba(0,0,0,0.5)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '12px',
        color: 'rgba(255,255,255,0.8)',
      }}
    >
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#10b981',
            boxShadow: '0 0 8px #10b981',
          }}
        />
        <strong>{isFa ? 'وضعیت' : 'Status'}:</strong>
        <span>{statusText}</span>
        {lastClickInfo && (
          <span style={{ color: '#fbbf24', fontSize: '10px' }}>{lastClickInfo}</span>
        )}
      </div>

      <div
        style={{
          display: 'flex',
          gap: '12px',
          fontSize: '11px',
          color: 'rgba(255,255,255,0.6)',
        }}
      >
        <span>🖱️ {isFa ? 'چپ+درگ: چرخش' : 'Left+Drag: Rotate'}</span>
        <span>🔍 {isFa ? 'اسکرول: زوم' : 'Scroll: Zoom'}</span>
        <span>✋ {isFa ? 'راست+درگ: حرکت' : 'Right+Drag: Pan'}</span>
      </div>
    </div>
  );
}
