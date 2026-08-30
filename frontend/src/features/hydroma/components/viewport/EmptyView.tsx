/**
 * EmptyView
 * ==========
 * Empty state when no terrain has been generated yet.
 *
 * @module features/hydroma/components/viewport/EmptyView
 */

import { Mountain } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export function EmptyView() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'rgba(255,255,255,0.5)',
        gap: '16px',
      }}
    >
      <Mountain size={80} style={{ opacity: 0.3 }} />
      <div style={{ fontSize: '18px', fontWeight: 700 }}>
        {isFa ? 'زمین سه‌بعدی آماده نیست' : 'No 3D Terrain Yet'}
      </div>
      <div
        style={{
          fontSize: '13px',
          maxWidth: '400px',
          textAlign: 'center',
        }}
      >
        {isFa
          ? 'از پنل سمت چپ پارامترها را انتخاب و Generate کنید. سپس می‌توانید با موس زمین را بچرخانید، زوم کنید و روی آن کلیک کنید.'
          : 'Select parameters and Generate from the left panel. Then you can rotate, zoom, and click on the terrain.'}
      </div>
    </div>
  );
}
