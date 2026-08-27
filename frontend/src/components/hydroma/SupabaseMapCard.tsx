import React, { useEffect, useRef, useState } from 'react';
import { MapPin } from 'lucide-react';
import { Deck } from '@deck.gl/core';
import { ScatterplotLayer } from '@deck.gl/layers';

interface LandscapeRow {
  id?: string;
  name?: string;
  province?: string | null;
  country?: string | null;
  geo_boundary?: { type?: string; coordinates?: [number, number] } | null;
}

interface SupabaseMapCardProps {
  lat: number;
  lon: number;
}

/**
 * فاز ۶-ب — مناطق واقعی از دیتابیس Supabase (platform_landscapes، ۲۱ ردیف)
 * با مختصات GeoJSON Point روی deck.gl. بدون داده -> حالت صادقانه.
 */
export const SupabaseMapCard: React.FC<SupabaseMapCardProps> = ({ lat, lon }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const deckRef = useRef<Deck | null>(null);
  const [rows, setRows] = useState<LandscapeRow[]>([]);
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch('/api/v1/supabase/landscapes');
        const d = (await res.json()) as { status?: string; count?: number; rows?: LandscapeRow[]; error?: string };
        if (!alive) return;
        if (d.status === 'ok') {
          setRows(d.rows ?? []);
          setStatus('ok');
        } else {
          setError(String(d.error ?? 'خطا'));
          setStatus('error');
        }
      } catch (err) {
        if (!alive) return;
        setError(err instanceof Error ? err.message : 'خطا');
        setStatus('error');
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const pts = rows
    .filter((r) => r.geo_boundary?.type === 'Point' && Array.isArray(r.geo_boundary.coordinates))
    .map((r) => ({ name: r.name ?? '—', province: r.province ?? '—', pos: r.geo_boundary!.coordinates as [number, number] }));

  useEffect(() => {
    if (!containerRef.current || status !== 'ok') return;
    const layer = new ScatterplotLayer({
      id: 'supabase-landscapes',
      data: pts,
      getPosition: (d: { pos: [number, number] }) => d.pos,
      getFillColor: [13, 148, 136, 200],
      getRadius: 700,
      radiusUnits: 'meters',
      stroked: true,
      getLineColor: [255, 255, 255, 220],
      lineWidthMinPixels: 1.5,
    });
    deckRef.current = new Deck({
      parent: containerRef.current,
      initialViewState: {
        longitude: pts.length > 0 ? pts[0].pos[0] : lon,
        latitude: pts.length > 0 ? pts[0].pos[1] : lat,
        zoom: 9,
        pitch: 0,
      },
      controller: true,
      layers: [layer],
    });
    return () => {
      deckRef.current?.finalize();
      deckRef.current = null;
    };
  }, [status, pts.length]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.7rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0d9488' }}>
          <MapPin size={17} /> مناطق واقعی (Supabase + PostGIS)
        </h3>
        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
          {status === 'ok' ? `${rows.length} منطقه از دیتابیس ابری` : '…'}
        </span>
      </div>

      {status === 'loading' && <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>در حال دریافت…</p>}
      {status === 'error' && <p style={{ fontSize: '0.82rem', color: '#ef4444' }}>⚠️ {error}</p>}

      {status === 'ok' && (
        <>
          {pts.length > 0 ? (
            <div ref={containerRef} style={{ width: '100%', height: 240, borderRadius: 12, overflow: 'hidden', background: '#0f172a' }} />
          ) : (
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', padding: '1rem 0' }}>
              هیچ ردیفی مختصات GeoJSON ندارد — پس از افزودن geo_boundary نقشه فعال میشود.
            </p>
          )}
          <div style={{ maxHeight: 160, overflowY: 'auto', marginTop: '0.6rem', fontSize: '0.76rem' }}>
            {rows.map((r) => (
              <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', padding: '0.28rem 0.1rem', borderBottom: '1px dashed var(--color-border)' }}>
                <span style={{ fontWeight: 600 }}>{r.name}</span>
                <span style={{ color: 'var(--color-text-secondary)' }}>
                  {r.province ?? '—'} · {r.geo_boundary?.type === 'Point' && r.geo_boundary.coordinates ? `${r.geo_boundary.coordinates[0]}, ${r.geo_boundary.coordinates[1]}` : 'بدون مختصات'}
                </span>
              </div>
            ))}
          </div>
          <p style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', margin: '0.5rem 0 0' }}>
            داده واقعی از جدول platform_landscapes (پروژه Supabase شما) — ستون geo_boundary GeoJSON آماده PostGIS است.
          </p>
        </>
      )}
    </div>
  );
};
