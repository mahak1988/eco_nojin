"use client";
import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import { Mountain } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';
import { useFarm } from '../../lib/farm-context';
import { api } from '../../lib/api-client';
import { useLeafletFix } from '../../lib/useLeafletFix';

// All Leaflet imports are DYNAMIC (SSR-safe)
const MapContainer = dynamic(
  () => import('react-leaflet').then(m => m.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then(m => m.TileLayer),
  { ssr: false }
);
const Rectangle = dynamic(
  () => import('react-leaflet').then(m => m.Rectangle),
  { ssr: false }
);
const Marker = dynamic(
  () => import('react-leaflet').then(m => m.Marker),
  { ssr: false }
);

interface GridCell {
  lat: number; lon: number; risk: number; loss: number;
  slope: number; rainfall: number;
}

const riskColor = (risk: number): string => {
  if (risk < 5) return '#10b981';
  if (risk < 15) return '#fbbf24';
  if (risk < 30) return '#f97316';
  return '#dc2626';
};

export default function ErosionRiskMap({ baseLat, baseLon }: { baseLat: number; baseLon: number }) {
  useLeafletFix();
  
  const { colors } = useTheme();
  const { selectedFarm } = useFarm();
  const [grid, setGrid] = useState<GridCell[]>([]);
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [params, setParams] = useState({
    texture: 'loam', c_factor: 0.5, p_factor: 0.8, rainfall: 450,
  });
  const [totalLoss, setTotalLoss] = useState(0);

  useEffect(() => { setMounted(true); }, []);
  useEffect(() => { generateRiskGrid(); }, [baseLat, baseLon, params.texture, params.c_factor, params.rainfall]);

  const generateRiskGrid = async () => {
    setLoading(true);
    const cells: GridCell[] = [];
    const gridSize = 4;  // Reduced from 6 to 4 for faster response
    const step = 0.01;

    for (let i = -gridSize; i <= gridSize; i++) {
      for (let j = -gridSize; j <= gridSize; j++) {
        const lat = baseLat + i * step;
        const lon = baseLon + j * step;
        const slopeBase = 3 + Math.abs(i) * 2 + Math.abs(j) * 1.5 + Math.random() * 3;
        const rainfallVar = params.rainfall * (0.8 + Math.random() * 0.4);

        try {
          const res = await api.get<any>(`/api/v1/soil/erosion?slope_length_m=${80 + Math.random() * 40}&slope_percent=${slopeBase}&annual_rainfall_mm=${rainfallVar}&texture=${params.texture}&c_factor=${params.c_factor}&p_factor=${params.p_factor}`);

          if (res.success && res.data) {
            cells.push({
              lat, lon,
              risk: res.data.annual_soil_loss_t_per_ha,
              loss: res.data.annual_soil_loss_t_per_ha,
              slope: slopeBase,
              rainfall: rainfallVar,
            });
          }
        } catch (e) {
          // Skip failed cells
        }
      }
    }

    setGrid(cells);
    setTotalLoss(cells.length > 0 ? cells.reduce((sum, c) => sum + c.loss, 0) / cells.length : 0);
    setLoading(false);
  };

  const lat = selectedFarm?.latitude || baseLat;
  const lon = selectedFarm?.longitude || baseLon;
  const cellSize = 0.01;

  return (
    <div style={{
      background: colors.cardBg, borderRadius: '20px',
      border: `1px solid ${colors.border}`, overflow: 'hidden',
    }}>
      <div style={{ padding: '20px', borderBottom: `1px solid ${colors.border}` }}>
        <h3 style={{ color: colors.text, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Mountain size={20} color={colors.warm} />
          Soil Erosion Risk Map (RUSLE)
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: colors.textMuted, display: 'block', marginBottom: '4px' }}>Soil Texture</label>
            <select value={params.texture}
              onChange={(e) => setParams({ ...params, texture: e.target.value })}
              style={{
                width: '100%', padding: '8px', borderRadius: '6px',
                border: `1px solid ${colors.border}`, background: colors.bg,
                color: colors.text, fontFamily: 'inherit', fontSize: '0.85rem',
              }}
            >
              <option value="sand">Sand</option>
              <option value="loam">Loam</option>
              <option value="clay">Clay</option>
              <option value="silt_loam">Silt Loam</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: colors.textMuted, display: 'block', marginBottom: '4px' }}>
              C Factor: {params.c_factor.toFixed(2)}
            </label>
            <input type="range" min="0.01" max="1" step="0.01"
              value={params.c_factor}
              onChange={(e) => setParams({ ...params, c_factor: parseFloat(e.target.value) })}
              style={{ width: '100%' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.75rem', color: colors.textMuted, display: 'block', marginBottom: '4px' }}>
              Rainfall: {params.rainfall}mm
            </label>
            <input type="range" min="100" max="2000" step="50"
              value={params.rainfall}
              onChange={(e) => setParams({ ...params, rainfall: parseInt(e.target.value) })}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
          <div style={{ padding: '10px', background: colors.bg, borderRadius: '10px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: colors.textMuted }}>Avg Loss</div>
            <div style={{ fontSize: '1.2rem', fontWeight: '800', color: colors.primary }}>
              {totalLoss.toFixed(1)}
            </div>
            <div style={{ fontSize: '0.7rem', color: colors.textMuted }}>t/ha/yr</div>
          </div>
          <div style={{ padding: '10px', background: colors.bg, borderRadius: '10px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: colors.textMuted }}>Cells</div>
            <div style={{ fontSize: '1.2rem', fontWeight: '800', color: colors.accent }}>
              {grid.length}
            </div>
          </div>
          <div style={{ padding: '10px', background: colors.bg, borderRadius: '10px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: colors.textMuted }}>Max Risk</div>
            <div style={{ fontSize: '1.2rem', fontWeight: '800', color: colors.danger }}>
              {grid.length > 0 ? Math.max(...grid.map(c => c.risk)).toFixed(1) : '0'}
            </div>
          </div>
          <div style={{ padding: '10px', background: colors.bg, borderRadius: '10px', textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: colors.textMuted }}>Texture</div>
            <div style={{ fontSize: '1rem', fontWeight: '700', color: colors.text, textTransform: 'capitalize' }}>
              {params.texture.replace('_', ' ')}
            </div>
          </div>
        </div>
      </div>

      <div style={{ height: '500px', position: 'relative' }}>
        {mounted ? (
          <MapContainer
            center={[lat, lon]} zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png" />
            <Marker position={[lat, lon]} />
            {grid.map((cell, i) => (
              <Rectangle
                key={i}
                bounds={[
                  [cell.lat - cellSize/2, cell.lon - cellSize/2],
                  [cell.lat + cellSize/2, cell.lon + cellSize/2],
                ]}
                pathOptions={{
                  fillColor: riskColor(cell.risk),
                  fillOpacity: 0.5,
                  weight: 1,
                  color: 'rgba(255,255,255,0.3)',
                }}
              />
            ))}
          </MapContainer>
        ) : (
          <div style={{
            height: '100%', width: '100%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: colors.bg, color: colors.textMuted,
          }}>
            Loading map...
          </div>
        )}

        <div style={{
          position: 'absolute', bottom: '30px', right: '10px',
          background: 'rgba(255,255,255,0.95)', padding: '12px',
          borderRadius: '8px', fontSize: '0.75rem', color: '#111',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          zIndex: 1000,
        }}>
          <div style={{ fontWeight: '700', marginBottom: '6px' }}>Risk Level (t/ha/yr)</div>
          {[
            { label: '< 5 (Low)', color: '#10b981' },
            { label: '5-15 (Moderate)', color: '#fbbf24' },
            { label: '15-30 (High)', color: '#f97316' },
            { label: '> 30 (Very High)', color: '#dc2626' },
          ].map((l, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px' }}>
              <div style={{ width: '12px', height: '12px', background: l.color, borderRadius: '2px' }} />
              <span>{l.label}</span>
            </div>
          ))}
        </div>

        {loading && (
          <div style={{
            position: 'absolute', inset: 0,
            background: 'rgba(0,0,0,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'white', fontSize: '1.1rem',
            zIndex: 2000,
          }}>
            Computing erosion grid...
          </div>
        )}
      </div>
    </div>
  );
}
