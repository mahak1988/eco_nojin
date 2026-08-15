"use client";
import { useState } from 'react';
import { motion } from 'framer-motion';
import { MapPin, Plus, ChevronDown, Leaf } from 'lucide-react';
import { useFarm } from '../../lib/farm-context';
import { useTheme } from '../../lib/theme-context';

export default function FarmSelector() {
  const { farms, selectedFarm, selectFarm, createFarm } = useFarm();
  const { colors } = useTheme();
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    name: '', latitude: 35.6892, longitude: 51.3890,
    area_hectares: 10, soil_type: 'loam', climate_zone: 'semi-arid',
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await createFarm(form);
    setCreating(false);
    setForm({ name: '', latitude: 35.6892, longitude: 51.3890, area_hectares: 10, soil_type: 'loam', climate_zone: 'semi-arid' });
  };

  return (
    <div style={{ position: 'relative' }}>
      <motion.button
        whileHover={{ scale: 1.02 }}
        onClick={() => setOpen(!open)}
        style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '8px 14px', borderRadius: '10px',
          background: colors.cardBg, border: `1px solid ${colors.border}`,
          color: colors.text, cursor: 'pointer',
          minWidth: '180px',
          backdropFilter: 'blur(10px)',
        }}
      >
        <Leaf size={16} color={colors.primary} />
        <span style={{ flex: 1, textAlign: 'start', fontSize: '0.9rem', fontWeight: '500' }}>
          {selectedFarm ? selectedFarm.name : 'Select Farm'}
        </span>
        <ChevronDown size={16} style={{ transform: open ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }} />
      </motion.button>

      {open && (
        <>
          <div onClick={() => setOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 50 }} />
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              position: 'absolute', top: 'calc(100% + 6px)', right: 0,
              width: '280px', background: colors.bgAlt,
              border: `1px solid ${colors.border}`,
              borderRadius: '12px', padding: '8px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
              zIndex: 100,
            }}
          >
            {farms.map(farm => (
              <motion.button
                key={farm.id}
                whileHover={{ x: 4 }}
                onClick={() => { selectFarm(farm); setOpen(false); }}
                style={{
                  width: '100%', padding: '10px 12px',
                  borderRadius: '8px', border: 'none',
                  background: selectedFarm?.id === farm.id ? `${colors.primary}15` : 'transparent',
                  color: colors.text, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '10px',
                  textAlign: 'start', fontFamily: 'inherit',
                  marginBottom: '4px',
                }}
              >
                <MapPin size={16} color={colors.primary} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: '600', fontSize: '0.9rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {farm.name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                    {farm.area_hectares} ha â€¢ {farm.soil_type || 'Unknown'}
                  </div>
                </div>
              </motion.button>
            ))}

            {!creating ? (
              <button
                onClick={() => setCreating(true)}
                style={{
                  width: '100%', padding: '10px', borderRadius: '8px',
                  border: `1px dashed ${colors.primary}`,
                  background: 'transparent', color: colors.primary,
                  cursor: 'pointer', marginTop: '4px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                  fontFamily: 'inherit', fontSize: '0.875rem', fontWeight: '500',
                }}
              >
                <Plus size={16} /> Add New Farm
              </button>
            ) : (
              <form onSubmit={handleCreate} style={{ padding: '8px', marginTop: '4px' }}>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Farm name" required
                  style={{
                    width: '100%', padding: '8px', borderRadius: '6px',
                    border: `1px solid ${colors.border}`, background: colors.bg,
                    color: colors.text, marginBottom: '6px', fontFamily: 'inherit', fontSize: '0.85rem',
                  }} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                  <input type="number" step="0.0001" value={form.latitude}
                    onChange={(e) => setForm({ ...form, latitude: parseFloat(e.target.value) })}
                    placeholder="Lat"
                    style={{
                      padding: '8px', borderRadius: '6px',
                      border: `1px solid ${colors.border}`, background: colors.bg,
                      color: colors.text, fontFamily: 'inherit', fontSize: '0.8rem',
                    }} />
                  <input type="number" step="0.0001" value={form.longitude}
                    onChange={(e) => setForm({ ...form, longitude: parseFloat(e.target.value) })}
                    placeholder="Lon"
                    style={{
                      padding: '8px', borderRadius: '6px',
                      border: `1px solid ${colors.border}`, background: colors.bg,
                      color: colors.text, fontFamily: 'inherit', fontSize: '0.8rem',
                    }} />
                </div>
                <input type="number" step="0.1" value={form.area_hectares}
                  onChange={(e) => setForm({ ...form, area_hectares: parseFloat(e.target.value) })}
                  placeholder="Hectares"
                  style={{
                    width: '100%', padding: '8px', borderRadius: '6px', marginTop: '6px',
                    border: `1px solid ${colors.border}`, background: colors.bg,
                    color: colors.text, fontFamily: 'inherit', fontSize: '0.85rem',
                  }} />
                <div style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
                  <button type="submit" style={{
                    flex: 1, padding: '8px', borderRadius: '6px',
                    background: colors.primary, color: 'white', border: 'none',
                    cursor: 'pointer', fontSize: '0.85rem', fontWeight: '600',
                  }}>Create</button>
                  <button type="button" onClick={() => setCreating(false)} style={{
                    flex: 1, padding: '8px', borderRadius: '6px',
                    background: colors.bg, color: colors.text,
                    border: `1px solid ${colors.border}`,
                    cursor: 'pointer', fontSize: '0.85rem',
                  }}>Cancel</button>
                </div>
              </form>
            )}
          </motion.div>
        </>
      )}
    </div>
  );
}
