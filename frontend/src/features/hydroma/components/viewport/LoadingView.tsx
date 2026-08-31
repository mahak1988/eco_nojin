/**
 * LoadingView
 * ============
 * Fullscreen loading state while DEM is being fetched.
 *
 * @module features/hydroma/components/viewport/LoadingView
 */

import { Loader2 } from 'lucide-react';
import { useHydromaStore } from '../../store';

export function LoadingView() {
  const siteMeta = useHydromaStore((s) => s.siteMeta);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '14px',
        color: 'rgba(255,255,255,0.75)',
      }}
    >
      <Loader2 size={46} className="spin" />
      <div style={{ fontSize: 15, fontWeight: 600 }}>در حال بارگذاری زمین واقعی از DEM…</div>
      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)' }}>
        Open-Meteo • Copernicus DEM 90m • سایت {siteMeta?.siteId || '---'}
      </div>
    </div>
  );
}
