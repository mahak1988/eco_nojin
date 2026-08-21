"use client";
import { lazy, Suspense, useState, useRef } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { motion, useMotionValue, useTransform } from 'framer-motion';
import Footer from '../../components/layout/Footer';
import ScenarioComparison from '../../components/charts/ScenarioComparison';
import ErosionRiskMap from '../../components/maps/ErosionRiskMap';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import { useAuth } from '../../lib/auth-context';
import { useFarm } from '../../lib/farm-context';
import FarmSelector from '../../components/farm/FarmSelector';
import {
  LayoutDashboard, Leaf, Satellite, Mountain, TrendingUp,
  ShoppingCart, TreePine, Droplet, Mic, Wallet,
  AlertTriangle,
} from 'lucide-react';

const BenchmarkPanel = lazy(() => import('../../components/BenchmarkPanel'));
const CarbonCreditPanel = lazy(() => import('../../components/CarbonCreditPanel'));
const ChatAssistant = lazy(() => import('../../components/ChatAssistant'));
const CropPlannerPanel = lazy(() => import('../../components/CropPlannerPanel'));
const EcoWalletPanel = lazy(() => import('../../components/EcoWalletPanel'));
const MarketplacePanel = lazy(() => import('../../components/MarketplacePanel'));
const MobileFeaturesPanel = lazy(() => import('../../components/MobileFeaturesPanel'));
const SatellitePanel = lazy(() => import('../../components/SatellitePanel'));
const ScenarioPanel = lazy(() => import('../../components/ScenarioPanel'));
const WatershedPanel = lazy(() => import('../../components/WatershedPanel'));

// بارگذاری کره زمین 3D فقط در سمت کلاینت
const GlobeMap = dynamic(() => import('@/components/maps/GlobeMap'), { ssr: false });

// ------------------ کامپوننت کارت 3D (جداسازی شده برای رعایت قانون هوک‌ها) ------------------
const ModuleCard = ({ mod, colors, t, index }: any) => {
  const Icon = mod.icon;
  const cardRef = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const rotateX = useTransform(y, [-100, 100], [20, -20]);
  const rotateY = useTransform(x, [-100, 100], [-20, 20]);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    x.set(e.clientX - centerX);
    y.set(e.clientY - centerY);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <Link key={mod.key} href={`/modules/${mod.key}`}>
      <motion.div
        ref={cardRef}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05 }}
        style={{
          rotateX,
          rotateY,
          transformStyle: "preserve-3d",
          padding: '20px',
          borderRadius: '16px',
          background: colors.cardBg,
          border: `1px solid ${colors.border}`,
          cursor: 'pointer',
          height: '100%',
        }}
        whileHover={{ y: -6, boxShadow: `0 20px 40px ${mod.color}30` }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: mod.gradient,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '12px',
            boxShadow: `0 8px 20px ${mod.color}40`,
            transform: "translateZ(20px)",
          }}
        >
          <Icon size={24} color="white" />
        </div>
        <div
          style={{
            fontWeight: '700',
            color: colors.text,
            fontSize: '1rem',
            marginBottom: '4px',
            textTransform: 'capitalize',
            transform: "translateZ(10px)",
          }}
        >
          {t(`${mod.key}_module_title`)}
        </div>
        <div
          style={{
            fontSize: '0.8rem',
            color: colors.textMuted,
            transform: "translateZ(5px)",
          }}
        >
          {t(`${mod.key}_module_desc`) || t('dashboard_click_to_explore')}
        </div>
      </motion.div>
    </Link>
  );
};

// ------------------ صفحه اصلی داشبورد ------------------
export default function DashboardPage() {
  const { t, direction } = useI18n();
  const { colors } = useTheme();
  const { user, isAuthenticated } = useAuth();
  const { selectedFarm, farms, selectFarm, createFarm } = useFarm();
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
                {isAuthenticated ? t('dashboard_greeting').replace('{name}', user?.full_name ?? '') : t('dashboard_hero_title')}
              <Link href="/dashboard/overview" className="ml-3 inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-bold text-white transition-opacity hover:opacity-90">
                نمای واقعی (API)
              </Link>
              </h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                {t('dashboard_hero_subtitle')}
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
            <h3 style={{ color: colors.text, marginBottom: '8px' }}>{t('dashboard_login_title')}</h3>
            <p style={{ color: colors.textMuted, marginBottom: '20px' }}>
              {t('dashboard_login_hint')}
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
                {t('dashboard_farms_count').replace('{count}', String(farms.length))}
              </h3>
              <FarmSelector />
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
                {showCreate ? t('dashboard_cancel') : t('dashboard_new_farm')}
              </motion.button>
            </div>

            {showCreate && (
              <form onSubmit={handleCreateFarm} style={{
                padding: '16px', background: colors.bg,
                borderRadius: '12px', marginBottom: '16px',
                display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px',
              }}>
                <input value={farmForm.name} onChange={(e) => setFarmForm({ ...farmForm, name: e.target.value })}
                  placeholder={t('dashboard_farm_name')} aria-label={t('dashboard_farm_name')} required
                  style={{ padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.cardBg, color: colors.text, fontFamily: 'inherit' }} />
                <input type="number" step="0.0001" value={farmForm.latitude}
                  onChange={(e) => setFarmForm({ ...farmForm, latitude: Number.parseFloat(e.target.value) })}
                  placeholder={t('dashboard_latitude')} aria-label={t('dashboard_latitude')}
                  style={{ padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.cardBg, color: colors.text, fontFamily: 'inherit' }} />
                <input type="number" step="0.0001" value={farmForm.longitude}
                  onChange={(e) => setFarmForm({ ...farmForm, longitude: Number.parseFloat(e.target.value) })}
                  placeholder={t('dashboard_longitude')} aria-label={t('dashboard_longitude')}
                  style={{ padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.cardBg, color: colors.text, fontFamily: 'inherit' }} />
                <input type="number" step="0.1" value={farmForm.area_hectares}
                  onChange={(e) => setFarmForm({ ...farmForm, area_hectares: Number.parseFloat(e.target.value) })}
                  placeholder={t('dashboard_hectares')} aria-label={t('dashboard_hectares')}
                  style={{ padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.cardBg, color: colors.text, fontFamily: 'inherit' }} />
                <motion.button type="submit"
                  whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                  style={{
                    padding: '10px', borderRadius: '8px',
                    background: colors.success, color: 'white', border: 'none',
                    cursor: 'pointer', fontWeight: '600',
                  }}>
                  {t('dashboard_create_farm')}
                </motion.button>
              </form>
            )}

            {farms.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '20px', color: colors.textMuted }}>
                {t('dashboard_no_farms')}
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
                      {farm.area_hectares} ha • {farm.soil_type || t('dashboard_unknown')}
                    </div>
                    {selectedFarm?.id === farm.id && (
                      <div style={{ fontSize: '0.7rem', color: colors.primary, marginTop: '6px', fontWeight: '600' }}>
                        {t('dashboard_active')}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* Module Grid (3D Tilt Cards) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{ marginBottom: '32px' }}
        >
          <h2 style={{ color: colors.text, marginBottom: '20px', fontSize: '1.5rem' }}>
            {t('dashboard_modules_title')}
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
            {modules.map((mod, i) => <ModuleCard key={mod.key} mod={mod} colors={colors} t={t} index={i} />)}
          </div>
        </motion.div>

        {/* Scenarios Comparison */}
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ marginBottom: '32px' }}>
          <h2 style={{ color: colors.text, marginBottom: '20px', fontSize: '1.5rem' }}>
            {t('dashboard_scenarios_title')}
          </h2>
          <ScenarioComparison />
        </motion.div>

        {/* Erosion Risk Map */}
        {selectedFarm && (
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <h2 style={{ color: colors.text, marginBottom: '20px', fontSize: '1.5rem' }}>
              {t('dashboard_erosion_title')}
            </h2>
            <ErosionRiskMap baseLat={selectedFarm.latitude} baseLon={selectedFarm.longitude} />
          </motion.div>
        )}

        {/* Globe Map 3D */}
        {selectedFarm && (
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ marginTop: '32px' }}>
            <h2 style={{ color: colors.text, marginBottom: '20px', fontSize: '1.5rem' }}>
              {t('Global 3D Map')}
            </h2>
            <GlobeMap 
              points={[{ 
                lat: selectedFarm.latitude, 
                lng: selectedFarm.longitude, 
                label: selectedFarm.name 
              }]} 
              height={400} 
            />
          </motion.div>
        )}

        {/* Interactive Panels */}
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} style={{ marginTop: '32px' }}>
          <h2 style={{ color: colors.text, marginBottom: '8px', fontSize: '1.5rem' }}>
            {t('dashboard_panels_title')}
          </h2>
          <p style={{ color: colors.textMuted, marginBottom: '20px', fontSize: '0.9rem' }}>
            {t('dashboard_panels_hint')}
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px', alignItems: 'start' }}>
            {[
              ['benchmark', BenchmarkPanel], ['carbon', CarbonCreditPanel], ['assistant', ChatAssistant], ['crop', CropPlannerPanel],
              ['wallet', EcoWalletPanel], ['marketplace', MarketplacePanel], ['mobile', MobileFeaturesPanel], ['satellite', SatellitePanel],
              ['scenario', ScenarioPanel], ['watershed', WatershedPanel],
            ].map(([id, Panel]) => (
              <Suspense key={id} fallback={
                <div aria-busy="true" style={{ padding: '24px', borderRadius: '12px', border: `1px solid ${colors.border}`, background: colors.cardBg, minHeight: '160px' }}>
                  <div style={{ width: '60%', height: '14px', borderRadius: '8px', background: `${colors.border}66`, marginBottom: '12px' }} />
                  <div style={{ width: '90%', height: '10px', borderRadius: '8px', background: `${colors.border}55`, marginBottom: '8px' }} />
                  <div style={{ width: '75%', height: '10px', borderRadius: '8px', background: `${colors.border}55` }} />
                </div>
              }>
                <Panel />
              </Suspense>
            ))}
          </div>
        </motion.div>
      </div>
      <Footer />
    </div>
  );
}