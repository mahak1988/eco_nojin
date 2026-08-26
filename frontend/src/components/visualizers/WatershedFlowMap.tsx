import React, { useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { ArcLayer } from '@deck.gl/layers';

interface WatershedFlowMapProps {
  center?: [number, number];
  zoom?: number;
  flowData?: Array<{
    source: [number, number];
    target: [number, number];
    value: number;
    type: 'river' | 'runoff' | 'groundwater';
  }>;
}

/**
 * SimpleFlowMap - نقشه جریان آب بدون وابگی به TileLayer
 * استفاده از ArcLayer با Canvas basemap
 * سازگار با تمام نسخه‌های Vite
 */
export const WatershedFlowMap: React.FC<WatershedFlowMapProps> = ({
  center = [51.4, 35.5],
  zoom = 10,
  flowData = [],
}) => {
  const sampleFlowData = useMemo(() => {
    if (flowData.length > 0) return flowData;
    
    const [lng, lat] = center;
    return [
      { source: [lng - 0.1, lat + 0.1], target: [lng, lat], value: 15, type: 'river' as const },
      { source: [lng + 0.08, lat + 0.12], target: [lng, lat], value: 12, type: 'river' as const },
      { source: [lng - 0.05, lat - 0.08], target: [lng, lat], value: 8, type: 'river' as const },
      { source: [lng + 0.05, lat + 0.05], target: [lng + 0.02, lat + 0.02], value: 3, type: 'runoff' as const },
      { source: [lng - 0.04, lat - 0.03], target: [lng - 0.01, lat - 0.01], value: 2, type: 'runoff' as const },
      { source: [lng + 0.1, lat], target: [lng + 0.05, lat - 0.05], value: 5, type: 'groundwater' as const },
    ];
  }, [flowData, center]);

  const layers = useMemo(() => {
    const riverFlows = sampleFlowData.filter((d) => d.type === 'river');
    const runoffFlows = sampleFlowData.filter((d) => d.type === 'runoff');
    const groundwaterFlows = sampleFlowData.filter((d) => d.type === 'groundwater');

    return [
      new ArcLayer({
        id: 'river-flow',
        data: riverFlows,
        getSourcePosition: (d: any) => d.source,
        getTargetPosition: (d: any) => d.target,
        getSourceColor: [30, 144, 255, 220],
        getTargetColor: [30, 144, 255, 100],
        getWidth: (d: any) => d.value * 100,
        getHeight: 0.3,
        pickable: true,
      }),
      new ArcLayer({
        id: 'runoff-arcs',
        data: runoffFlows,
        getSourcePosition: (d: any) => d.source,
        getTargetPosition: (d: any) => d.target,
        getSourceColor: [239, 68, 68, 200],
        getTargetColor: [239, 68, 68, 80],
        getWidth: (d: any) => d.value * 120,
        getHeight: 0.2,
        pickable: true,
      }),
      new ArcLayer({
        id: 'groundwater-flow',
        data: groundwaterFlows,
        getSourcePosition: (d: any) => d.source,
        getTargetPosition: (d: any) => d.target,
        getSourceColor: [16, 185, 129, 180],
        getTargetColor: [16, 185, 129, 60],
        getWidth: (d: any) => d.value * 140,
        getHeight: 0.1,
        pickable: true,
      }),
    ];
  }, [sampleFlowData]);

  const totalFlow = sampleFlowData.reduce((sum, d) => sum + d.value, 0);

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      height: 500,
      borderRadius: 'var(--radius-lg)',
      overflow: 'hidden',
      background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a3d 50%, #1a4d3a 100%)',
    }}>
      {/* Grid Pattern Overlay */}
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: `
          linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)
        `,
        backgroundSize: '50px 50px',
        zIndex: 0,
      }} />

      <DeckGL
        initialViewState={{
          longitude: center[0],
          latitude: center[1],
          zoom,
          pitch: 30,
          bearing: -15,
        }}
        controller={true}
        layers={layers}
        style={{ position: 'relative', zIndex: 1 }}
        getTooltip={({ object }: any) =>
          object && {
            html: `
              <div style="padding: 8px; font-family: Vazirmatn, sans-serif; direction: rtl;">
                <strong>${
                  object.type === 'river' ? '🌊 رودخانه' :
                  object.type === 'runoff' ? '⚠️ رواناب' : '💧 زیرزمینی'
                }</strong><br/>
                دبی: <b>${object.value} m³/s</b>
              </div>
            `,
            style: {
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              fontSize: '0.875rem',
              borderRadius: '8px',
              color: '#171717',
            },
          }
        }
      />

      {/* Legend */}
      <div style={{
        position: 'absolute',
        top: 20,
        right: 20,
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        padding: '1rem',
        borderRadius: 'var(--radius-lg)',
        fontSize: '0.875rem',
        boxShadow: 'var(--shadow-md)',
        minWidth: 220,
        zIndex: 10,
      }}>
        <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: 700 }}>
          🌊 جریان آب حوضه
        </h4>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <div style={{ width: 30, height: 4, background: '#1e90ff', borderRadius: 2 }} />
          <span>رودخانه</span>
          <strong style={{ marginLeft: 'auto' }}>
            {sampleFlowData.filter((d) => d.type === 'river').reduce((s, d) => s + d.value, 0)} m³/s
          </strong>
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

        <div style={{
          borderTop: '1px solid var(--color-border)',
          paddingTop: '0.5rem',
          fontWeight: 700,
          display: 'flex',
          justifyContent: 'space-between',
        }}>
          <span>مجموع:</span>
          <span style={{ color: 'var(--color-primary)' }}>{totalFlow} m³/s</span>
        </div>
      </div>

      {/* Center marker */}
      <div style={{
        position: 'absolute',
        bottom: 20,
        left: 20,
        background: 'rgba(0, 0, 0, 0.6)',
        backdropFilter: 'blur(8px)',
        padding: '0.5rem 0.75rem',
        borderRadius: 'var(--radius-md)',
        fontSize: '0.75rem',
        color: 'white',
        fontFamily: 'monospace',
        zIndex: 10,
      }}>
        📍 {center[1].toFixed(4)}, {center[0].toFixed(4)} | Zoom: {zoom}
      </div>
    </div>
  );
};
