import React, { useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { FlowLayer, ArcLayer } from '@deck.gl/layers';
import { StaticMap } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

interface WatershedFlowMapProps {
  center?: [number, number]; // [lng, lat]
  zoom?: number;
  flowData?: Array<{
    source: [number, number];
    target: [number, number];
    value: number; // m³/s
    type: 'river' | 'runoff' | 'groundwater';
  }>;
}

/**
 * نقشه جریان آب در حوضه آبخیز
 * استفاده از deck.gl برای نمایش جریان‌های پویا
 */
export const WatershedFlowMap: React.FC<WatershedFlowMapProps> = ({
  center = [51.4, 35.5], // ایران مرکزی
  zoom = 10,
  flowData = [],
}) => {
  // داده‌های نمونه اگر خالی بود
  const sampleFlowData = useMemo(() => {
    if (flowData.length > 0) return flowData;
    
    const [lng, lat] = center;
    return [
      // جریان‌های اصلی رودخانه
      { source: [lng - 0.1, lat + 0.1], target: [lng, lat], value: 15, type: 'river' as const },
      { source: [lng + 0.08, lat + 0.12], target: [lng, lat], value: 12, type: 'river' as const },
      { source: [lng - 0.05, lat - 0.08], target: [lng, lat], value: 8, type: 'river' as const },
      // رواناب سطحی
      { source: [lng + 0.05, lat + 0.05], target: [lng + 0.02, lat + 0.02], value: 3, type: 'runoff' as const },
      { source: [lng - 0.04, lat - 0.03], target: [lng - 0.01, lat - 0.01], value: 2, type: 'runoff' as const },
      // جریان زیرزمینی
      { source: [lng + 0.1, lat], target: [lng + 0.05, lat - 0.05], value: 5, type: 'groundwater' as const },
    ];
  }, [flowData, center]);

  const layers = useMemo(() => {
    const riverFlows = sampleFlowData.filter((d) => d.type === 'river');
    const runoffFlows = sampleFlowData.filter((d) => d.type === 'runoff');
    const groundwaterFlows = sampleFlowData.filter((d) => d.type === 'groundwater');

    return [
      // جریان‌های اصلی رودخانه
      new FlowLayer({
        id: 'river-flow',
        data: riverFlows,
        getSourcePosition: (d: any) => d.source,
        getTargetPosition: (d: any) => d.target,
        getThickness: (d: any) => d.value * 0.3,
        getColor: () => [30, 144, 255, 180],
        speed: 2,
        opacity: 0.8,
      }),

      // رواناب سطحی (قرمز - خطر)
      new ArcLayer({
        id: 'runoff-arcs',
        data: runoffFlows,
        getSourcePosition: (d: any) => d.source,
        getTargetPosition: (d: any) => d.target,
        getSourceColor: [239, 68, 68, 200],
        getTargetColor: [239, 68, 68, 100],
        getWidth: (d: any) => d.value * 2,
        getHeight: 0.3,
      }),

      // جریان زیرزمینی (سبز - تغذیه آبخوان)
      new FlowLayer({
        id: 'groundwater-flow',
        data: groundwaterFlows,
        getSourcePosition: (d: any) => d.source,
        getTargetPosition: (d: any) => d.target,
        getThickness: (d: any) => d.value * 0.5,
        getColor: () => [16, 185, 129, 150],
        speed: 0.5,
        opacity: 0.6,
      }),
    ];
  }, [sampleFlowData]);

  const totalFlow = sampleFlowData.reduce((sum, d) => sum + d.value, 0);
  const riverFlow = sampleFlowData
    .filter((d) => d.type === 'river')
    .reduce((sum, d) => sum + d.value, 0);

  return (
    <div style={{ position: 'relative', width: '100%', height: 500, borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
      <DeckGL
        initialViewState={{
          longitude: center[0],
          latitude: center[1],
          zoom,
          pitch: 45,
          bearing: -20,
        }}
        controller={true}
        layers={layers}
      >
        <StaticMap
          mapStyle="https://demotiles.maplibre.org/style.json"
          reuseMaps
        />
      </DeckGL>

      {/* Legend */}
      <div
        style={{
          position: 'absolute',
          top: 20,
          right: 20,
          background: 'rgba(255, 255, 255, 0.95)',
          padding: '1rem',
          borderRadius: 'var(--radius-lg)',
          fontSize: '0.875rem',
          boxShadow: 'var(--shadow-md)',
          minWidth: 200,
        }}
      >
        <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem' }}>🌊 جریان آب حوضه</h4>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <div style={{ width: 30, height: 4, background: '#1e90ff', borderRadius: 2 }} />
          <span>رودخانه</span>
          <strong style={{ marginLeft: 'auto' }}>{riverFlow} m³/s</strong>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <div style={{ width: 30, height: 3, background: '#ef4444', borderRadius: 2 }} />
          <span>رواناب</span>
          <strong style={{ marginLeft: 'auto', color: '#ef4444' }}>
            {sampleFlowData.filter((d) => d.type === 'runoff').reduce((s, d) => s + d.value, 0)} m³/s
          </strong>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <div style={{ width: 30, height: 3, background: '#10b981', borderRadius: 2 }} />
          <span>زیرزمینی</span>
          <strong style={{ marginLeft: 'auto', color: '#10b981' }}>
            {sampleFlowData.filter((d) => d.type === 'groundwater').reduce((s, d) => s + d.value, 0)} m³/s
          </strong>
        </div>

        <div
          style={{
            borderTop: '1px solid var(--color-border)',
            paddingTop: '0.5rem',
            fontWeight: 700,
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <span>مجموع:</span>
          <span>{totalFlow} m³/s</span>
        </div>
      </div>
    </div>
  );
};
