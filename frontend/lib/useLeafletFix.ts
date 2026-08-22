/**
 * useLeafletFix - Fix Leaflet default marker icons in Next.js SSR.
 * 
 * Strategy: dynamic import inside useEffect so it only runs on client.
 * This prevents "window is not defined" errors during SSR.
 * 
 * Usage: Call useLeafletFix() at the top of any component that uses Leaflet.
 */
import { useEffect, useRef } from 'react';

let fixed = false;

export function useLeafletFix() {
  const hasRun = useRef(false);
  
  useEffect(() => {
    if (hasRun.current || fixed) {
      hasRun.current = true;
      return;
    }
    hasRun.current = true;
    fixed = true;

    // Dynamic import - only runs on client
    import('leaflet').then((L) => {
      const leaflet = L.default || L;
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment -- leaflet types lack the patched method - accessing internal property
      if ((leaflet.Icon.Default as any)?.prototype?._getIconUrl !== undefined) {
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment -- leaflet types lack the patched method
        delete (leaflet.Icon.Default as any).prototype._getIconUrl;
      }
      (leaflet.Icon.Default as any).mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      });
    }).catch(err => {
      console.warn('Leaflet fix failed:', err);
    });
  }, []);
}

export default useLeafletFix;
