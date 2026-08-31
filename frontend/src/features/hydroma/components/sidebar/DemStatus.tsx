/**
 * DemStatus
 * ==========
 * DEM loading indicator and error display.
 *
 * @module features/hydroma/components/sidebar/DemStatus
 */

import { Loader2 } from 'lucide-react';
import { useHydromaStore } from '../../store';

export function DemStatus() {
  const demLoading = useHydromaStore((s) => s.demLoading);
  const demError = useHydromaStore((s) => s.demError);

  return (
    <>
      {demLoading && (
        <div
          style={{
            fontSize: '11px',
            color: '#81C784',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Loader2 size={12} className="spin" /> در حال دریافت DEM واقعی…
        </div>
      )}

      {demError && <div style={{ fontSize: '11px', color: '#fca5a5' }}>{demError}</div>}
    </>
  );
}
