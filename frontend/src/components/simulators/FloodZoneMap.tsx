import React, { useEffect, useRef } from 'react';
import { Deck } from '@deck.gl/core';
import { ScatterplotLayer } from '@deck.gl/layers';
import { MapPin, AlertTriangle } from 'lucide-react';
import type { NdviGridPoint } from '../../types/vll';

export interface FloodCell {
  x: number;
  y: number;
  depthM: number;
}

interface FloodZoneMapProps {
  lat: number;
  lon: number;
  ndviGrid?: NdviGridPoint[];
  floodCells?: FloodCell[];
  floodStatus?: string;
  floodEngine?: string;
  floodWseM?: number;
  requiresHecrasInstall?: boolean;
  height?: number;
}

const ndviColor = (v: number): [number, number, number, number] => {
  const t = Math.max(0, Math.min(1, (v + 0.2) / 0.8));
  return [Math.round(34 + 105 * (1 - t)), Math.round(120 + 95 * t), 34, 200];
};

const floodColor = (d: FloodCell): [number, number, number, number] => {
  const t = Math.max(0, Math.min(1, d.depthM / 1.5));
  return [Math.round(30 + 200 * t), Math.round(110 + 40 * (1 - t)), 220, 180];
};

/**
 * نقشه سیلاب با deck.gl — لایه NDVI واقعی (Sentinel-2) و لایه عمق سیلاب HEC-RAS.
 * وقتی خروجی واقعی HEC-RAS موجود نباشد، فقط وضعیت صادقانه + مقدار Manning نمایش داده می‌شود
 * (هیچ داده ساختگی روی مسیر واقعی قرار نمی‌گیرد — W-001).
 */
export const FloodZoneMap: React.FC<FloodZoneMapProps> = ({
  lat,
  lon,
  ndviGrid,
  floodCells = [],
  floodStatus,
  floodEngine,
  floodWseM,
  requiresHecrasInstall,
  height = 360,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const deckRef = useRef<Deck | null>(null);

  const hasNdvi = !!ndviGrid && ndviGrid.length > 0;
  const hasFlood = floodCells.length > 0;

  useEffect(() => {
    if (!containerRef.current) return;

    const ndviLayer = hasNdvi
      ? new ScatterplotLayer({
          id: 'ndvi',
          data: ndviGrid,
          getPosition: (d: NdviGridPoint) => [d.lon, d.lat],
          getFillColor: (d: NdviGridPoint) => ndviColor(d.ndvi),
          getRadius: 250,
          radiusUnits: 'meters',
          stroked: false,
        })
      : null;

    const floodLayer = hasFlood
      ? new ScatterplotLayer({
          id: 'flood',
          data: floodCells,
          getPosition: (d: FloodCell) => [lon + d.x, lat + d.y],
          getFillColor: (d: FloodCell) => floodColor(d),
          getRadius: 300,
          radiusUnits: 'meters',
          stroked: false,
        })
      : null;

    deckRef.current = new Deck({
      parent: containerRef.current,
      initialViewState: {
        longitude: lon,
        latitude: lat,
        zoom: 12,
        pitch: 0,
      },
      controller: true,
      layers: [ndviLayer, floodLayer].filter((l) => l !== null) as ScatterplotLayer[],
    });

    return () => {
      deckRef.current?.finalize();
      deckRef.current = null;
    };
  }, [lat, lon, hasNdvi, hasFlood, ndviGrid, floodCells]);

  return (
    <div>
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height,
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          position: 'relative',
          background: '#0f172a',
        }}
      />
      {/* Legend / status overlay */}
      <div style={{ position: 'relative' }}>
        <div
          style={{
            position: 'absolute',
            top: 10,
            left: 10,
            background: 'rgba(15,23,42,0.85)',
            color: '#e2e8f0',
            padding: '0.5rem 0.8rem',
            borderRadius: 10,
            fontSize: '0.78rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            zIndex: 2,
            pointerEvents: 'none',
          }}
        >
          <MapPin size={13} color="#22c55e" />
          {lat.toFixed(3)}°N, {lon.toFixed(3)}°E
        </div>

        {!hasFlood && (
          <div
            style={{
              position: 'absolute',
              top: 10,
              right: 10,
              background: 'rgba(245,158,11,0.15)',
              border: '1px solid rgba(245,158,11,0.4)',
              color: '#fbbf24',
              padding: '0.5rem 0.8rem',
              borderRadius: 10,
              fontSize: '0.78rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              zIndex: 2,
              maxWidth: 260,
              pointerEvents: 'none',
            }}
          >
            <AlertTriangle size={13} />
            <span>
              {requiresHecrasInstall
                ? `خروجی واقعی HEC-RAS در دسترس نیست (باینری نصب نشده). مقدار تقریبی Manning: ${floodWseM?.toFixed(2) ?? '—'} m`
                : floodStatus === 'ok'
                  ? 'لایه سیلاب — خروجی HEC-RAS'
                  : 'لایه سیلاب فعال نیست'}
            </span>
          </div>
        )}

        {!hasNdvi && !hasFlood && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(15,23,42,0.55)',
              color: '#94a3b8',
              fontSize: '0.85rem',
              zIndex: 1,
              pointerEvents: 'none',
              borderRadius: 'var(--radius-lg)',
            }}
          >
            نقشه پایه — لایه‌ها پس از در دسترس بودن داده واقعی (NDVI: اعتبارنامه CDSE · سیلاب:
            باینری HEC-RAS) نمایش داده می‌شوند
          </div>
        )}
      </div>
      <p style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', marginTop: '0.4rem' }}>
        موتور: {floodEngine ?? '—'} · مدل: deck.gl 9.3 · لایه NDVI فقط با داده واقعی Sentinel-2
      </p>
    </div>
  );
};
