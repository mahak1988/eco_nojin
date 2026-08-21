"use client";
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Plus, ChevronDown, Leaf } from 'lucide-react';
import { useFarm } from '../../lib/farm-context';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';

export default function FarmSelector() {
  const { t } = useI18n();
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
      {/* Trigger Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setOpen(!open)}
        style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '8px 14px', borderRadius: '10px',
          background: open ? `${colors.primary}15` : colors.cardBg,
          border: open ? `1.5px solid ${colors.primary}` : `1px solid ${colors.border}`,
          color: colors.text, cursor: 'pointer',
          minWidth: '160px', // کمی انعطاف‌پذیرتر
          backdropFilter: 'blur(10px)',
          transition: 'all 0.2s ease',
        }}
      >
        <Leaf size={16} color={colors.primary} />
        <span style={{ flex: 1, textAlign: 'start', fontSize: '0.9rem', fontWeight: '500' }}>
          {selectedFarm ? selectedFarm.name : t('farm_selector_select')}
        </span>
        <ChevronDown 
          size={16} 
          color={colors.textMuted}
          style={{ 
            transform: open ? 'rotate(180deg)' : 'rotate(0)', 
            transition: 'transform 0.3s ease' 
          }} 
        />
      </motion.button>

      {/* Dropdown Menu with Glassmorphism */}
      <AnimatePresence>
        {open && (
          <>
            <div onClick={() => setOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 50 }} />
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              style={{
                position: 'absolute', top: 'calc(100% + 8px)', right: 0,
                width: '300px',
                background: colors.cardBg + 'dd',
                backdropFilter: 'blur(16px)',
                border: `1px solid ${colors.border}`,
                borderRadius: '16px',
                padding: '8px',
                boxShadow: '0 20px 50px rgba(0,0,0,0.2)',
                zIndex: 100,
              }}
            >
              {/* List of Farms */}
              {farms.map(farm => {
                const isActive = selectedFarm?.id === farm.id;
                return (
                  <motion.button
                    key={farm.id}
                    whileHover={{ x: 6, background: `${colors.primary}10` }}
                    onClick={() => { selectFarm(farm); setOpen(false); }}
                    style={{
                      width: '100%', padding: '10px 12px',
                      borderRadius: '10px', border: 'none',
                      background: isActive ? `${colors.primary}15` : 'transparent',
                      color: colors.text, cursor: 'pointer',
                      display: 'flex', alignItems: 'center', gap: '10px',
                      textAlign: 'start', fontFamily: 'inherit',
                      marginBottom: '4px', position: 'relative',
                      transition: 'background 0.2s ease',
                    }}
                  >
                    {/* Active Indicator Line */}
                    {isActive && (
                      <motion.div
                        layoutId="farmActiveIndicator"
                        transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                        style={{
                          position: 'absolute',
                          left: 0, top: '50%',
                          transform: 'translateY(-50%)',
                          width: '3px', height: '20px',
                          background: colors.primary,
                          borderRadius: '0 3px 3px 0',
                        }}
                      />
                    )}
                    
                    <MapPin size={16} color={colors.primary} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: '600', fontSize: '0.9rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {farm.name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                        {farm.area_hectares} ha • {farm.soil_type || 'Unknown'}
                      </div>
                    </div>
                  </motion.button>
                );
              })}

              {/* Create New Farm Section */}
              {!creating ? (
                <motion.button
                  whileHover={{ scale: 1.02, background: `${colors.primary}10` }}
                  onClick={() => setCreating(true)}
                  style={{
                    width: '100%', padding: '12px 10px', borderRadius: '10px',
                    border: `1px dashed ${colors.primary}`,
                    background: 'transparent', color: colors.primary,
                    cursor: 'pointer', marginTop: '6px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                    fontFamily: 'inherit', fontSize: '0.875rem', fontWeight: '500',
                    transition: 'all 0.2s',
                  }}
                >
                  <Plus size={16} /> {t('Add New Farm')}
                </motion.button>
              ) : (
                <motion.form
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  onSubmit={handleCreate}
                  style={{ padding: '12px 8px', marginTop: '6px' }}
                >
                  <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                    aria-label={t('dashboard_farm_name')} placeholder={t('dashboard_farm_name')} required
                    style={{
                      width: '100%', padding: '10px', borderRadius: '8px',
                      border: `1px solid ${colors.border}`, background: colors.bg,
                      color: colors.text, marginBottom: '8px', fontFamily: 'inherit', fontSize: '0.85rem',
                      outline: 'none', transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.currentTarget.style.borderColor = colors.primary}
                    onBlur={(e) => e.currentTarget.style.borderColor = colors.border}
                  />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <input type="number" step="0.0001" value={form.latitude}
                      onChange={(e) => setForm({ ...form, latitude: parseFloat(e.target.value) })}
                      aria-label={t('dashboard_latitude')} placeholder={t('dashboard_latitude')}
                      style={{
                        padding: '10px', borderRadius: '8px',
                        border: `1px solid ${colors.border}`, background: colors.bg,
                        color: colors.text, fontFamily: 'inherit', fontSize: '0.8rem',
                        outline: 'none', transition: 'border-color 0.2s',
                      }}
                      onFocus={(e) => e.currentTarget.style.borderColor = colors.primary}
                      onBlur={(e) => e.currentTarget.style.borderColor = colors.border}
                    />
                    <input type="number" step="0.0001" value={form.longitude}
                      onChange={(e) => setForm({ ...form, longitude: parseFloat(e.target.value) })}
                      aria-label={t('dashboard_longitude')} placeholder={t('dashboard_longitude')}
                      style={{
                        padding: '10px', borderRadius: '8px',
                        border: `1px solid ${colors.border}`, background: colors.bg,
                        color: colors.text, fontFamily: 'inherit', fontSize: '0.8rem',
                        outline: 'none', transition: 'border-color 0.2s',
                      }}
                      onFocus={(e) => e.currentTarget.style.borderColor = colors.primary}
                      onBlur={(e) => e.currentTarget.style.borderColor = colors.border}
                    />
                  </div>
                  <input type="number" step="0.1" value={form.area_hectares}
                    onChange={(e) => setForm({ ...form, area_hectares: parseFloat(e.target.value) })}
                    aria-label={t('dashboard_hectares')} placeholder={t('dashboard_hectares')}
                    style={{
                      width: '100%', padding: '10px', borderRadius: '8px', marginTop: '8px',
                      border: `1px solid ${colors.border}`, background: colors.bg,
                      color: colors.text, fontFamily: 'inherit', fontSize: '0.85rem',
                      outline: 'none', transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.currentTarget.style.borderColor = colors.primary}
                    onBlur={(e) => e.currentTarget.style.borderColor = colors.border}
                  />
                  <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                    <motion.button
                      whileHover={{ scale: 1.02, boxShadow: `0 4px 12px ${colors.primary}30` }}
                      whileTap={{ scale: 0.95 }}
                      type="submit"
                      style={{
                        flex: 1, padding: '10px', borderRadius: '8px',
                        background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                        color: 'white', border: 'none',
                        cursor: 'pointer', fontSize: '0.85rem', fontWeight: '600',
                      }}
                    >
                      {t('Create')}
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.95 }}
                      type="button"
                      onClick={() => setCreating(false)}
                      style={{
                        flex: 1, padding: '10px', borderRadius: '8px',
                        background: colors.bg, color: colors.text,
                        border: `1px solid ${colors.border}`,
                        cursor: 'pointer', fontSize: '0.85rem',
                      }}
                    >
                      {t('Cancel')}
                    </motion.button>
                  </div>
                </motion.form>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}