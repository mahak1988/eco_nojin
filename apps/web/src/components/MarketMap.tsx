'use client';

import { useEffect, useRef, useState } from 'react';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import type { BazaarType, MarketProfile } from '@/types/bazaar-types';

export interface MarketMapProps {
  bazaars: BazaarType[];
  marketProfiles?: MarketProfile[];
  locale: string;
  onBazaarClick?: (bazaar: BazaarType) => void;
  height?: number;
  center?: { lat: number; lon: number };
  zoom?: number;
}

/**
 * MapLibre 5 market map — reusable for /{locale}/market/bazaars
 * (regional hub, §5.3 کانون منطقه‌ای).
 *
 * Shows bazaar polygons with popup + ProvenanceStamp.
 * Scaffold: requires MapLibre CSS + JS to be loaded (next/dynamic or <link> in layout).
 */
export function MarketMap({
  bazaars,
  marketProfiles,
  locale,
  onBazaarClick,
  height = 480,
  center,
  zoom = 8,
}: MarketMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const [mapReady, setMapReady] = useState(false);
  const [selectedBazaar, setSelectedBazaar] = useState<BazaarType | null>(null);
  const centerLat = center?.lat;
  const centerLon = center?.lon;

  useEffect(() => {
    const container = mapContainerRef.current;
    if (!container) return;

    let cancelled = false;
    let map: { remove: () => void } | null = null;
    setMapReady(false);

    const loadMap = async () => {
      try {
        const maplibre = await import('maplibre-gl');
        if (cancelled) return;

        const instance = new maplibre.Map({
          container,
          style: 'https://demotiles.maplibre.org/style.json',
          center:
            centerLat !== undefined && centerLon !== undefined
              ? [centerLon, centerLat]
              : [52.0, 35.0],
          zoom,
        });
        map = instance;

        instance.on('load', () => {
          if (!cancelled) setMapReady(true);
        });

        instance.on('click', (event) => {
          const features = instance.queryRenderedFeatures([event.point.x, event.point.y], {
            layers: ['bazaars'],
          });
          const rawBazaarId = features[0]?.properties?.id;
          const bazaarId =
            typeof rawBazaarId === 'string' || typeof rawBazaarId === 'number'
              ? String(rawBazaarId)
              : undefined;
          const bazaar = bazaarId ? bazaars.find((item) => item.id === bazaarId) : undefined;
          if (bazaar) {
            setSelectedBazaar(bazaar);
            onBazaarClick?.(bazaar);
          }
        });
      } catch {
        if (!cancelled) setMapReady(false);
      }
    };

    void loadMap();

    return () => {
      cancelled = true;
      map?.remove();
    };
  }, [bazaars, centerLat, centerLon, onBazaarClick, zoom]);

  const rtl = locale === 'fa' || locale === 'ar';

  return (
    <div className="market-map" dir={rtl ? 'rtl' : 'ltr'}>
      <ProvenanceStamp source="maplibre-market-map" label="نقشه بازارها">
        <h2 className="sr-only">Map</h2>
      </ProvenanceStamp>
      <div
        ref={mapContainerRef}
        className="w-full rounded-lg border border-line overflow-hidden"
        style={{ height }}
        role="application"
        aria-label={locale === 'fa' ? 'نقشه بازارها' : 'Bazaars map'}
      >
        {!mapReady && (
          <div className="flex items-center justify-center h-full bg-surface text-ink-soft text-sm">
            {locale === 'fa' ? 'در حال بارگذاری نقشه…' : 'Loading map…'}
            <span className="ml-2 num">({bazaars.length} بازار)</span>
          </div>
        )}
      </div>

      {/* Bazaar popup (scaffold) */}
      {selectedBazaar && (
        <div
          className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-80 bg-background border border-line rounded-lg shadow-lg p-4 z-20"
          role="dialog"
          aria-label={selectedBazaar.name}
        >
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-ink">{selectedBazaar.name}</h3>
            <button
              type="button"
              onClick={() => setSelectedBazaar(null)}
              className="text-xs text-ink-soft hover:text-ink"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
          <div className="mt-2 text-xs text-ink-soft space-y-1">
            <div className="num">کد: {selectedBazaar.code}</div>
            <div>{selectedBazaar.bazaar_type}</div>
            <div>
              {locale === 'fa' ? 'فروشگاه‌ها:' : 'Stores:'} {selectedBazaar.store_count}
            </div>
            <div>{selectedBazaar.status}</div>
          </div>
        </div>
      )}

      {/* Legend (scaffold) */}
      <div className="mt-2 flex items-center gap-4 text-xs text-ink-soft">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-primary" />
          {locale === 'fa' ? 'بازارچه' : 'Bazaar'}
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm border border-primary" />
          {locale === 'fa' ? 'محدوده' : 'Boundary'}
        </span>
        <span className="num">
          {bazaars.length} {locale === 'fa' ? 'بازار' : 'bazaars'}
          {marketProfiles && marketProfiles.length > 0
            ? ` · ${marketProfiles.length} ${locale === 'fa' ? 'کانون' : 'hub'}`
            : ''}
        </span>
      </div>
    </div>
  );
}
