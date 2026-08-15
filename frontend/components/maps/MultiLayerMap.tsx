"use client";
import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import { Layers, CloudRain, Thermometer } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';
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
const Marker = dynamic(
  () => import('react-leaflet').then(m => m.Marker),
  { ssr: false }
);
const Popup = dynamic(
  () => import('react-leaflet').then(m => m.Popup),
  { ssr: false }
);

interface Props {
  lat: number; lon: number;
  height?: string;
  showWeatherData?: boolean;
}

const LAYERS = [
  {
    id: 'street', name: 'Street', icon: '🗺️',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '© OpenStreetMap',
  },
  {
    id: 'topo', name: 'Topographic', icon: '⛰️',
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: '© OpenTopoMap',
  },
  {
    id: 'satellite', name: 'Satellite', icon: '🛰️',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '© Esri',
  },
  {
    id: 'terrain', name: 'Terrain', icon: '🏔️',
    url: 'https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg',
    attribution: '© Stamen',
  },
];

export default function MultiLayerMap({ lat, lon, height = '450px', showWeatherData = true }: Props) {
  useLeafletFix();
  
  const { colors } = useTheme();
  const [activeLayer, setActiveLayer] = useState('topo');
  const [weatherData, setWeatherData] = useState<any>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);
  useEffect(() => { if (showWeatherData) fetchWeather(); }, [lat, lon]);

  const fetchWeather = async () => {
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,soil_temperature_0cm,soil_moisture_0_to_1cm&hourly=temperature_2m,precipitation,soil_temperature_0cm,soil_moisture_0_to_1cm&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration&timezone=auto&forecast_days=7`;
      const res = await fetch(url);
      const data = await res.json();
      setWeatherData(data);
    } catch (e) {
      console.error('Weather fetch failed:', e);
    }
  };

  const layer = LAYERS.find(l => l.id === activeLayer) || LAYERS[0];
  const current = weatherData?.current;

  const weatherCodeToIcon = (code: number) => {
    if (code === 0) return '☀️';
    if (code <= 3) return '⛅';
    if (code <= 48) return '🌫️';
    if (code <= 67) return '🌧️';
    if (code <= 77) return '🌨️';
    if (code <= 82) return '🌦️';
    if (code <= 86) return '❄️';
    return '⛈️';
  };

  return (
    <div style={{
      background: colors.cardBg, borderRadius: '20px',
      border: `1px solid ${colors.border}`, overflow: 'hidden',
      backdropFilter: 'blur(20px)',
    }}>
      {/* Layer selector */}
      <div style={{
        padding: '12px 16px', display: 'flex', gap: '8px',
        borderBottom: `1px solid ${colors.border}`, flexWrap: 'wrap',
      }}>
        <Layers size={18} color={colors.text} style={{ marginRight: '4px' }} />
        {LAYERS.map(l => (
          <motion.button
            key={l.id}
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={() => setActiveLayer(l.id)}
            style={{
              padding: '6px 14px', borderRadius: '8px',
              background: activeLayer === l.id
                ? `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`
                : colors.bg,
              color: activeLayer === l.id ? 'white' : colors.text,
              border: activeLayer === l.id ? 'none' : `1px solid ${colors.border}`,
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px',
              fontSize: '0.85rem', fontWeight: '500', fontFamily: 'inherit',
            }}
          >
            <span>{l.icon}</span> {l.name}
          </motion.button>
        ))}
      </div>

      {/* Map */}
      <div style={{ height, position: 'relative' }}>
        {mounted ? (
          <MapContainer
            center={[lat, lon]} zoom={11}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer url={layer.url} attribution={layer.attribution} />
            <Marker position={[lat, lon]}>
              <Popup>
                <div style={{ color: '#111', fontSize: '0.85rem', minWidth: '160px' }}>
                  <strong style={{ color: colors.primary }}>Selected Location</strong><br />
                  Lat: {lat.toFixed(4)}<br />
                  Lon: {lon.toFixed(4)}
                  {current && (
                    <>
                      <br /><hr style={{ margin: '6px 0' }} />
                      <strong>Current:</strong> {current.temperature_2m}°C
                      <br />{weatherCodeToIcon(current.weather_code)}
                    </>
                  )}
                </div>
              </Popup>
            </Marker>
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
          position: 'absolute', bottom: '30px', left: '10px',
          background: 'rgba(255,255,255,0.95)', padding: '6px 10px',
          borderRadius: '6px', fontSize: '0.75rem', color: '#111',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          fontFamily: 'monospace',
          zIndex: 1000,
        }}>
          📍 {lat.toFixed(4)}, {lon.toFixed(4)}
        </div>
      </div>

      {/* Weather Data Panel */}
      {showWeatherData && current && (
        <div style={{ padding: '16px', borderTop: `1px solid ${colors.border}` }}>
          <h4 style={{ color: colors.text, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CloudRain size={18} color={colors.accent} />
            Real-time Environmental Data
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px' }}>
            {[
              { label: 'Air Temp', value: `${current.temperature_2m}°C`, icon: <Thermometer size={16} />, color: '#ef4444' },
              { label: 'Feels Like', value: `${current.apparent_temperature}°C`, icon: <span>🌡️</span>, color: '#f59e0b' },
              { label: 'Humidity', value: `${current.relative_humidity_2m}%`, icon: <span>💧</span>, color: '#3b82f6' },
              { label: 'Wind', value: `${current.wind_speed_10m} km/h`, icon: <span>💨</span>, color: '#06b6d4' },
              { label: 'Precipitation', value: `${current.precipitation} mm`, icon: <span>🌧️</span>, color: '#6366f1' },
              { label: 'Soil Temp', value: `${current.soil_temperature_0cm}°C`, icon: <span>🌱</span>, color: '#10b981' },
              { label: 'Soil Moisture', value: `${(current.soil_moisture_0_to_1cm * 100).toFixed(1)}%`, icon: <span>💦</span>, color: '#0ea5e9' },
              { label: 'Condition', value: weatherCodeToIcon(current.weather_code), icon: null, color: '#fbbf24' },
            ].map((item, i) => (
              <motion.div
                key={i}
                whileHover={{ y: -2 }}
                style={{
                  padding: '10px', background: colors.bg,
                  borderRadius: '10px', border: `1px solid ${colors.border}`,
                }}
              >
                <div style={{ fontSize: '0.7rem', color: colors.textMuted, marginBottom: '4px' }}>
                  {item.label}
                </div>
                <div style={{ fontSize: '1.1rem', fontWeight: '700', color: item.color, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {item.icon}
                  {item.value}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
