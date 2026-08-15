"use client";
import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import { MapPin, Search, Locate, Crosshair } from 'lucide-react';
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

// MapClickHandler must also be dynamic since it uses useMapEvents
const MapClickHandler = dynamic(
  () => import('./MapClickHandler'),
  { ssr: false }
);

interface Props {
  lat: number; lon: number;
  onChange: (lat: number, lon: number, address?: string) => void;
  height?: string;
}

export default function CoordinatePicker({ lat, lon, onChange, height = '300px' }: Props) {
  useLeafletFix();
  
  const { colors } = useTheme();
  const [manualLat, setManualLat] = useState(lat.toString());
  const [manualLon, setManualLon] = useState(lon.toString());
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [reverseAddress, setReverseAddress] = useState<string>('');
  const [mounted, setMounted] = useState(false);
  const [mapError, setMapError] = useState(false);

  useEffect(() => { setMounted(true); }, []);
  
  useEffect(() => {
    setManualLat(lat.toString());
    setManualLon(lon.toString());
    reverseGeocode(lat, lon);
  }, [lat, lon]);

  const reverseGeocode = async (lt: number, ln: number) => {
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lt}&lon=${ln}&zoom=14`,
        { headers: { 'Accept-Language': 'en,fa' } }
      );
      const data = await res.json();
      if (data.display_name) {
        const short = data.display_name.split(',').slice(0, 3).join(',');
        setReverseAddress(short);
      }
    } catch {}
  };

  const searchPlace = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=5`,
        { headers: { 'Accept-Language': 'en,fa' } }
      );
      const data = await res.json();
      setSearchResults(data);
    } catch {}
    setSearching(false);
  };

  const useCurrentLocation = () => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => onChange(pos.coords.latitude, pos.coords.longitude),
      (err) => alert('Could not get location: ' + err.message)
    );
  };

  const applyManual = () => {
    const lt = parseFloat(manualLat);
    const ln = parseFloat(manualLon);
    if (!isNaN(lt) && !isNaN(ln) && lt >= -90 && lt <= 90 && ln >= -180 && ln <= 180) {
      onChange(lt, ln);
    }
  };

  return (
    <div style={{
      background: colors.cardBg, borderRadius: '16px',
      border: `1px solid ${colors.border}`, overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{ padding: '16px', borderBottom: `1px solid ${colors.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <MapPin size={18} color={colors.primary} />
          <span style={{ fontWeight: '700', color: colors.text }}>Location</span>
        </div>

        {/* Search */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && searchPlace()}
            placeholder="Search city, region..."
            style={{
              flex: 1, padding: '8px 12px', borderRadius: '8px',
              border: `1px solid ${colors.border}`, background: colors.bg,
              color: colors.text, fontFamily: 'inherit', fontSize: '0.85rem',
            }}
          />
          <motion.button
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={searchPlace} disabled={searching}
            style={{
              padding: '8px 14px', borderRadius: '8px',
              background: colors.accent, color: 'white', border: 'none',
              cursor: 'pointer', fontSize: '0.85rem',
            }}
          >
            <Search size={14} style={{ display: 'inline' }} />
            {' '}{searching ? '...' : 'Search'}
          </motion.button>
        </div>

        {searchResults.length > 0 && (
          <div style={{
            maxHeight: '150px', overflowY: 'auto',
            background: colors.bg, borderRadius: '8px',
            border: `1px solid ${colors.border}`, marginBottom: '10px',
          }}>
            {searchResults.map((r, i) => (
              <button
                key={i}
                onClick={() => {
                  onChange(parseFloat(r.lat), parseFloat(r.lon), r.display_name);
                  setSearchResults([]);
                  setSearchQuery('');
                }}
                style={{
                  width: '100%', padding: '8px 12px',
                  background: 'transparent', border: 'none',
                  borderBottom: i < searchResults.length - 1 ? `1px solid ${colors.border}` : 'none',
                  textAlign: 'start', cursor: 'pointer', fontFamily: 'inherit',
                  color: colors.text, fontSize: '0.8rem',
                }}
              >
                {r.display_name?.slice(0, 80)}
              </button>
            ))}
          </div>
        )}

        {/* Manual input */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '8px', marginBottom: '10px' }}>
          <input
            type="number" step="0.0001" value={manualLat}
            onChange={(e) => setManualLat(e.target.value)}
            placeholder="Latitude"
            style={{
              padding: '8px', borderRadius: '6px',
              border: `1px solid ${colors.border}`, background: colors.bg,
              color: colors.text, fontFamily: 'inherit', fontSize: '0.85rem',
            }}
          />
          <input
            type="number" step="0.0001" value={manualLon}
            onChange={(e) => setManualLon(e.target.value)}
            placeholder="Longitude"
            style={{
              padding: '8px', borderRadius: '6px',
              border: `1px solid ${colors.border}`, background: colors.bg,
              color: colors.text, fontFamily: 'inherit', fontSize: '0.85rem',
            }}
          />
          <motion.button
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={applyManual}
            style={{
              padding: '8px 12px', borderRadius: '6px',
              background: colors.primary, color: 'white', border: 'none',
              cursor: 'pointer', fontSize: '0.8rem',
            }}
          >Apply</motion.button>
        </div>

        <motion.button
          whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
          onClick={useCurrentLocation}
          style={{
            width: '100%', padding: '8px', borderRadius: '6px',
            background: `${colors.accent}20`, color: colors.accent,
            border: `1px solid ${colors.accent}40`,
            cursor: 'pointer', display: 'flex', alignItems: 'center',
            justifyContent: 'center', gap: '6px', fontSize: '0.8rem',
          }}
        >
          <Locate size={14} /> Use My Location
        </motion.button>

        {reverseAddress && (
          <div style={{
            marginTop: '10px', padding: '8px 10px',
            background: `${colors.primary}10`, borderRadius: '6px',
            fontSize: '0.75rem', color: colors.text,
          }}>
            📍 {reverseAddress}
          </div>
        )}
      </div>

      {/* Map */}
      <div style={{ height, position: 'relative' }}>
        {mounted && !mapError ? (
          <MapContainer
            center={[lat, lon]} zoom={12}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution="© OSM"
            />
            <MapClickHandler onClick={(lt, ln) => onChange(lt, ln)} />
            <Marker position={[lat, lon]} />
          </MapContainer>
        ) : (
          <div style={{
            height: '100%', width: '100%',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            background: colors.bg, color: colors.textMuted, padding: '20px',
          }}>
            {mapError ? (
              <>
                <div style={{ marginBottom: '10px' }}>⚠️ Map failed to load</div>
                <div style={{ fontSize: '0.8rem' }}>Use manual coordinates above</div>
              </>
            ) : (
              <div>Loading map...</div>
            )}
          </div>
        )}
        <div style={{
          position: 'absolute', top: '10px', left: '10px',
          background: colors.cardBg, padding: '6px 10px',
          borderRadius: '6px', fontSize: '0.75rem',
          color: colors.text, boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          display: 'flex', alignItems: 'center', gap: '6px',
          zIndex: 1000,
        }}>
          <Crosshair size={12} color={colors.primary} />
          Click map to select
        </div>
      </div>
    </div>
  );
}
