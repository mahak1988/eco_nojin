"use client";
import { useEffect, useState } from 'react';
import Link from 'next/link';
import Navbar from '../../components/layout/Navbar';
import Footer from '../../components/layout/Footer';
import ScenarioComparison from '../../components/charts/ScenarioComparison';
import ErosionRiskMap from '../../components/maps/ErosionRiskMap';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import { useAuth } from '../../lib/auth-context';
import { useFarm } from '../../lib/farm-context';
import { api } from '../../lib/api-client';
import { motion } from 'framer-motion';
import {
  LayoutDashboard, Leaf, Satellite, Mountain, TrendingUp,
  ShoppingCart, TreePine, Droplet, Mic, Wallet,
  AlertTriangle, CheckCircle2, ArrowRight,
} from 'lucide-react';

export default function DashboardPage() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();
  const { user, isAuthenticated } = useAuth();
  const { selectedFarm, farms, selectFarm, refreshFarms, createFarm } = useFarm();
  const [farmForm, setFarmForm] = useState({
    name: '', latitude: 35.6892, longitude: 51.3890,
    area_hectares: 10, soil_type: 'loam', climate_zone: 'semi-arid',
  });
  const [showCreate, setShowCreate] = useState(false);

  const modules = [
    { key: 'soil', icon: Leaf, color: '#f97316', gradient: 'linear-gradient(135deg, #f97316, #fbbf24)' },
    { key: 'satellite', icon: Satellite, color: '#0ea5e9', gradient: 'linear-gradient(135deg, #0ea5e9, #0284c7)' },
    { key: 'erosion', icon: Mountain, color: '#f59e0b', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)' },
    { key: 'scenarios', icon: TrendingUp, color: '#fbbf24', gradient: 'linear-gradient(135deg, #fbbf24, #f59e0b)' },
    { key: 'marketplace', icon: ShoppingCart, color: '#fb7185', gradient: 'linear-gradient(135deg, #fb7185, #e11d48)' },
    { key: 'carbon', icon: TreePine, color: '#0d9488', gradient: 'linear-gradient(135deg, #0d9488, #0f766e)' },
    { key: 'watershed', icon: Droplet, color: '#38bdf8', gradient: 'linear-gradient(135deg, #38bdf8, #0284c7)' },
    { key: 'voice', icon: Mic, color: '#ec4899', gradient: 'linear-gradient(135deg, #ec4899, #db2777)' },
    { key: 'ecowallet', icon: Wallet, color: '#8b5cf6', gradient: 'linear-gradient(135deg, #fbbf24, #8b5cf6)' },
  ];

  const handleCreateFarm = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await createFarm(farmForm);
    if (res.success) {
      setShowCreate(false);
      setFarmForm({ name: '', latitude: 35.6892, longitude: 51.3890, area_hectares: 10, soil_type: 'loam', climate_zone: 'semi-arid' });
    }
  };

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <Navbar />
      <div style={{ maxWidth: '1500px', margin: '0 auto', padding: '32px 20px' }}>
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
            padding: '32px', borderRadius: '24px', color: 'white',
            marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <LayoutDashboard size={40} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>
                {isAuthenticated ? `Welcome, ${user?.full_name}!` : 'Eco Nojin Dashboard'}
              </h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                Integrated landscape management and analysis platform
              </p>
            </div>
          </div>
        </motion.div>

        {/* Farm Selection */}
        {!isAuthenticated ? (
          <div style={{
            padding: '40px', background: colors.cardBg, borderRadius: '20px',
            border: `1px solid ${colors.border}`, textAlign: 'center',
            marginBottom: '32px',
          }}>
            <AlertTriangle size={48} color={colors.warm} style={{ marginBottom: '16px' }} />
            <h3 style={{ color: colors.text, marginBottom: '8px' }}>Please login to continue</h3>
            <p style={{ color: colors.textMuted, marginBottom: '20px' }}>
              Create an account to save your farms and analyses
            </p>
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            style={{
              background: colors.cardBg, padding: '24px', borderRadius: '20px',
              border: `1px solid ${colors.border}`, marginBottom: '32px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
              <h3 style={{ color: colors.text, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                ًںŒ¾ Your Farms ({farms.length})
              </h3>
              <motion.button
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={() => setShowCreate(!showCreate)}
                style={{
                  padding: '8px 16px', borderRadius: '10px',
                  background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                  color: 'white', border: 'none', cursor: 'pointer',
                  fontSize: '0.85rem', fontWeight: '600',
                }}
              >
                {showCreate ? 'Cancel' : '+ New Farm'}
              </motion.button>
            </div>

            {showCreate && (
              <form onSubmit={handleCreateFarm} style={{
                padding: '16px', background: colors.bg,
                borderRadius: '12px', marginBottom: '16px',
                display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px',
              }}>
                <input value={farmForm.name} onChange={(e) => setFarmForm({ ...farmForm, name: e.target.value })}
                  placeholder="Farm name" required
                  style={{ padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.cardBg, color: colors.text, fontFamily: 'inherit' }} />
                <input type="number" step="0.0001" value={farmForm.latitude}
                  onChange={(e) => setFarmForm({ ...farmForm, latitude: parseFloat(e.target.value) })}
                  placeholder="Latitude"
                  style={{ padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.cardBg, color: colors.text, fontFamily: 'inherit' }} />
                <input type="number" step="0.0001" value={farmForm.longitude}
                  onChange={(e) => setFarmForm({ ...farmForm, longitude: parseFloat(e.target.value) })}
                  placeholder="Longitude"
                  style={{ padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.cardBg, color: colors.text, fontFamily: 'inherit' }} />
                <input type="number" step="0.1" value={farmForm.area_hectares}
                  onChange={(e) => setFarmForm({ ...farmForm, area_hectares: parseFloat(e.target.value) })}
                  placeholder="Hectares"
                  style={{ padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.cardBg, color: colors.text, fontFamily: 'inherit' }} />
                <motion.button type="submit"
                  whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                  style={{
                    padding: '10px', borderRadius: '8px',
                    background: colors.success, color: 'white', border: 'none',
                    cursor: 'pointer', fontWeight: '600',
                  }}>
                  Create Farm
                </motion.button>
              </form>
            )}

            {farms.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px', color: colors.textMuted }}>
                No farms yet. Create your first farm to start analyzing!
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
                {farms.map(farm => (
                  <motion.div
                    key={farm.id}
                    whileHover={{ y: -2 }}
                    onClick={() => selectFarm(farm)}
                    style={{
                      padding: '14px', borderRadius: '12px',
                      background: selectedFarm?.id === farm.id
                        ? `linear-gradient(135deg, ${colors.primary}20, ${colors.accent}20)`
                        : colors.bg,
                      border: selectedFarm?.id === farm.id
                        ? `2px solid ${colors.primary}`
                        : `1px solid ${colors.border}`,
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ fontWeight: '700', color: colors.text, marginBottom: '4px' }}>
                      {farm.name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                      {farm.area_hectares} ha â€¢ {farm.soil_type || 'Unknown'}
                    </div>
                    {selectedFarm?.id === farm.id && (
                      <div style={{ fontSize: '0.7rem', color: colors.primary, marginTop: '6px', fontWeight: '600' }}>
                        âœ“ Active
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* Module Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{ marginBottom: '32px' }}
        >
          <h2 style={{ color: colors.text, marginBottom: '20px', fontSize: '1.5rem' }}>
            ًںژ¯ Analysis Modules
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
            {modules.map((mod, i) => {
              const Icon = mod.icon;
              return (
                <Link key={mod.key} href={`/modules/${mod.key}`}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    whileHover={{ y: -6, boxShadow: `0 20px 40px ${mod.color}30` }}
                    style={{
                      padding: '20px', borderRadius: '16px',
                      background: colors.cardBg,
                      border: `1px solid ${colors.border}`,
                      cursor: 'pointer', height: '100%',
                      backdropFilter: 'blur(20px)',
                    }}
                  >
                    <div style={{
                      width: '48px', height: '48px', borderRadius: '12px',
                      background: mod.gradient, display: 'flex',
                      alignItems: 'center', justifyContent: 'center',
                      marginBottom: '12px',
                      boxShadow: `0 8px 20px ${mod.color}40`,
                    }}>
                      <Icon size={24} color="white" />
                    </div>
                    <div style={{ fontWeight: '700', color: colors.text, fontSize: '1rem', marginBottom: '4px', textTransform: 'capitalize' }}>
                      {mod.key}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: colors.textMuted }}>
                      {t(`module_${mod.key}_desc`) || 'Click to explore'}
                    </div>
                  </motion.div>
                </Link>
              );
            })}
          </div>
        </motion.div>

        {/* Scenarios Comparison */}
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ marginBottom: '32px' }}>
          <h2 style={{ color: colors.text, marginBottom: '20px', fontSize: '1.5rem' }}>
            ًں“ˆ Climate Scenario Analysis (2030-2100)
          </h2>
          <ScenarioComparison />
        </motion.div>

        {/* Erosion Risk Map */}
        {selectedFarm && (
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <h2 style={{ color: colors.text, marginBottom: '20px', fontSize: '1.5rem' }}>
              ًںŒچ Erosion Risk Heatmap
            </h2>
            <ErosionRiskMap baseLat={selectedFarm.latitude} baseLon={selectedFarm.longitude} />
          </motion.div>
        )}
      </div>
      <Footer />
    </div>
  );
}
