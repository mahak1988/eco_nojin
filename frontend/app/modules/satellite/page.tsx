"use client";
import { useState, useEffect } from 'react';
import Navbar from '../../../components/layout/Navbar';
import Footer from '../../../components/layout/Footer';
import IndicesRadar from '../../../components/visualizations/IndicesRadar';
import CoordinatePicker from '../../../components/maps/CoordinatePicker';
import MultiLayerMap from '../../../components/maps/MultiLayerMap';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { useFarm } from '../../../lib/farm-context';
import { api } from '../../../lib/api-client';
import { motion } from 'framer-motion';
import { Satellite, Leaf, Droplet, Flame, Map as MapIcon } from 'lucide-react';

export default function SatellitePage() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();
  const { selectedFarm } = useFarm();

  const [location, setLocation] = useState({ lat: 35.6892, lon: 51.3890 });
  const [bands, setBands] = useState({
    red: 0.2, nir: 0.5, blue: 0.1, green: 0.3, swir: 0.2,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    if (selectedFarm) {
      setLocation({ lat: selectedFarm.latitude, lon: selectedFarm.longitude });
    }
  }, [selectedFarm]);

  useEffect(() => { analyze(); }, [bands, location]);

  const analyze = async () => {
    setLoading(true);
    const res = await api.post<any>('/api/v1/satellite/analyze', {
      lat: location.lat, lon: location.lon,
      ...bands,
      farm_id: selectedFarm?.id,
    });
    if (res.success) setResult(res.data);
    setLoading(false);
  };

  const indices = result?.indices || {};
  const health = result?.vegetation_health || '';
  const healthColor = health.includes('very dense') || health.includes('healthy') ? colors.success
    : health.includes('dense') ? colors.accent
    : health.includes('moderate') ? colors.warm
    : colors.danger;

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <Navbar />
      <div style={{ maxWidth: '1500px', margin: '0 auto', padding: '32px 20px' }}>
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, ${colors.accent}, ${colors.primary})`,
            padding: '32px', borderRadius: '24px', color: 'white',
            marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Satellite size={40} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>{t('module_satellite')}</h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                Multi-layer analysis: Topographic, Thermal, Weather, Satellite
              </p>
            </div>
          </div>
        </motion.div>

        {/* Grid: Left controls + Right map */}
        <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '24px', marginBottom: '24px' }}>
          {/* Left: Coordinate Picker + Band Sliders */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <CoordinatePicker
              lat={location.lat} lon={location.lon}
              onChange={(lat, lon) => setLocation({ lat, lon })}
              height="280px"
            />

            {/* Band Controls */}
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              style={{
                background: colors.cardBg, padding: '20px', borderRadius: '20px',
                border: `1px solid ${colors.border}`,
              }}
            >
              <h4 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                ًںژ¨ Band Reflectance
              </h4>
              {Object.entries(bands).map(([band, val]) => {
                const bandColors: Record<string, string> = {
                  red: '#ef4444', nir: '#8b5cf6', blue: '#3b82f6',
                  green: '#10b981', swir: '#f59e0b',
                };
                return (
                  <div key={band} style={{ marginBottom: '14px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '0.85rem', color: colors.text, textTransform: 'uppercase', fontWeight: '600' }}>
                        {band}
                      </span>
                      <span style={{ fontSize: '0.85rem', color: bandColors[band], fontWeight: '700' }}>
                        {val.toFixed(2)}
                      </span>
                    </div>
                    <input
                      type="range" min="0" max="1" step="0.01" value={val}
                      onChange={(e) => setBands({ ...bands, [band]: parseFloat(e.target.value) })}
                      style={{
                        width: '100%', height: '6px', borderRadius: '3px',
                        background: `linear-gradient(90deg, ${bandColors[band]} 0%, ${bandColors[band]} ${val*100}%, ${colors.border} ${val*100}%)`,
                        appearance: 'none', cursor: 'pointer',
                      }}
                    />
                  </div>
                );
              })}
            </motion.div>
          </div>

          {/* Right: Multi-layer Map */}
          <MultiLayerMap lat={location.lat} lon={location.lon} height="680px" />
        </div>

        {/* Results Row */}
        {result && (
          <>
            {/* Health Banner */}
            <motion.div
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              style={{
                background: `linear-gradient(135deg, ${healthColor}20, ${healthColor}10)`,
                padding: '24px', borderRadius: '20px',
                border: `2px solid ${healthColor}40`,
                display: 'flex', alignItems: 'center', gap: '20px',
                marginBottom: '24px',
              }}
            >
              <div style={{
                width: '64px', height: '64px', borderRadius: '50%',
                background: healthColor, display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: `0 8px 24px ${healthColor}50`,
              }}>
                <Leaf size={32} color="white" />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.85rem', color: colors.textMuted }}>Vegetation Health</div>
                <div style={{ fontSize: '1.5rem', fontWeight: '800', color: healthColor, textTransform: 'capitalize' }}>
                  {health}
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>NDVI</div>
                <div style={{ fontSize: '2rem', fontWeight: '800', color: healthColor }}>
                  {indices.ndvi?.toFixed(2)}
                </div>
              </div>
            </motion.div>

            {/* Charts row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
              {/* Radar */}
              <motion.div
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                style={{
                  background: colors.cardBg, padding: '24px', borderRadius: '20px',
                  border: `1px solid ${colors.border}`,
                }}
              >
                <h4 style={{ color: colors.text, marginBottom: '16px' }}>Indices Radar</h4>
                <IndicesRadar
                  ndvi={indices.ndvi || 0} evi={indices.evi || 0}
                  savi={indices.savi || 0} ndwi={indices.ndwi || 0}
                  nbr={indices.nbr || 0}
                />
              </motion.div>

              {/* Index Cards */}
              <div style={{ display: 'grid', gridTemplateRows: 'repeat(5, 1fr)', gap: '10px' }}>
                {[
                  { key: 'ndvi', label: 'NDVI', desc: 'Vegetation', icon: Leaf, color: '#10b981' },
                  { key: 'evi', label: 'EVI', desc: 'Enhanced', icon: Leaf, color: '#06b6d4' },
                  { key: 'savi', label: 'SAVI', desc: 'Soil-Adj.', icon: Leaf, color: '#8b5cf6' },
                  { key: 'ndwi', label: 'NDWI', desc: 'Water', icon: Droplet, color: '#3b82f6' },
                  { key: 'nbr', label: 'NBR', desc: 'Burn', icon: Flame, color: '#ef4444' },
                ].map(({ key, label, desc, icon: Icon, color }) => (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
                    whileHover={{ x: -4 }}
                    style={{
                      background: colors.cardBg, padding: '14px 20px', borderRadius: '14px',
                      border: `1px solid ${colors.border}`,
                      display: 'flex', alignItems: 'center', gap: '16px',
                    }}
                  >
                    <Icon size={24} color={color} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '700', color: colors.text }}>{label}</div>
                      <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>{desc}</div>
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '800', color }}>
                      {indices[key]?.toFixed(3)}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
      <Footer />
    </div>
  );
}
