import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LogOut, User, Box, X } from 'lucide-react';
import { AnimatedLogo } from '../components/branding/AnimatedLogo';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { toggleTheme } from '../hooks/useThemeMode';
import { RealLandSummaryCard } from '../components/hydroma/RealLandSummaryCard';
import { ScientificChainPanel } from '../components/hydroma/ScientificChainPanel';
import { LiveMetricStrip } from '../components/hydroma/LiveMetricStrip';
import { HydromaModules } from '../components/hydroma/HydromaModules';
import { MrvCard } from '../components/hydroma/MrvCard';
import { LabCompareCard } from '../components/hydroma/LabCompareCard';
import { EconomyCard } from '../components/hydroma/EconomyCard';
import { SupabaseMapCard } from '../components/hydroma/SupabaseMapCard';
import { MarketplaceCard } from '../components/hydroma/MarketplaceCard';
import { LmsCard } from '../components/hydroma/LmsCard';
import { AuditCard } from '../components/hydroma/AuditCard';
import { ProfileCard } from '../components/hydroma/ProfileCard';
import { AdminCard } from '../components/hydroma/AdminCard';
import type { SceneMode } from '../components/hydroma/DashboardScene3D';
import type { RealLandResult, ScientificChainResult } from '../types/vll';

// صحنه سه‌بعدی — lazy تا باندل ورودی کوچک بماند
const DashboardScene3D = React.lazy(() => import('../components/hydroma/DashboardScene3D').then((m) => ({ default: m.DashboardScene3D })));

/**
 * داشبورد هیدروما — کاملاً مبتنی بر بک‌اند/موتورهای واقعی:
 * داده زنده (ERA5/SoilGrids/CDSE) + زنجیره علمی (RUSLE/RothC/AquaCrop/Pywr/HEC-RAS/NSGA-II/SWAT+)
 * با متریک‌های انیمیشنی، چارت در هر ماژول و شبیه‌ساز سه‌بعدی برای هر ماژول.
 * هیچ fallback ساختگی — مقادیر غایب «—».
 */
export const HydromaDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [realLand, setRealLand] = useState<RealLandResult | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lon: number }>({ lat: 35.5, lon: 51.5 });
  const [chain, setChain] = useState<ScientificChainResult | null>(null);
  const [sceneMode, setSceneMode] = useState<SceneMode>('idle');
  const [sceneOpen, setSceneOpen] = useState(false);

  const open3D = (mode: SceneMode) => {
    setSceneMode(mode);
    setSceneOpen(true);
  };

  return (
    <div className="hydroma-bg" style={{ minHeight: '100vh' }}>
      {/* Top bar */}
      <header className="glass" style={{ position: 'sticky', top: 0, zIndex: 50, padding: '0.9rem 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)' }}>
        <AnimatedLogo size="sm" showSubtitle={false} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Button variant="ghost" onClick={toggleTheme}>🌓</Button>
          <span className="badge badge-info"><User size={12} /> {user?.name}</span>
          <Button variant="ghost" onClick={logout} icon={<LogOut size={15} />}>خروج</Button>
        </div>
      </header>

      {/* Water hero */}
      <section style={{ position: 'relative', padding: '2.5rem 2rem 4.5rem', overflow: 'hidden', textAlign: 'center' }}>
        <div className="hydroma-waves" />
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ position: 'relative', zIndex: 1 }}>
          <h1 style={{ fontSize: '1.9rem', fontWeight: 800, color: '#fff', marginBottom: '0.5rem' }}>
            خوش آمدی، {user?.name} 🌍
          </h1>
          <p style={{ color: '#bae6fd', fontSize: '1rem' }}>
            داشبورد زنده HyDroMa — اقلیم، خاک، ماهواره و ۷ موتور علمی واقعی در یک نگاه
          </p>
        </motion.div>
      </section>

      <main style={{ maxWidth: 1500, margin: '-2rem auto 0', padding: '0 1.5rem 4rem', position: 'relative', zIndex: 2 }}>
        {/* Real data + chain controls */}
        <div className="grid grid-cols-2" style={{ marginBottom: '1.5rem', alignItems: 'start', gap: '1.2rem' }}>
          <RealLandSummaryCard onLoaded={setRealLand} onCoordsChange={(lat: number, lon: number) => setCoords({ lat, lon })} />
          <ScientificChainPanel lat={coords.lat} lon={coords.lon} onResult={setChain} />
        </div>

        {/* Live animated metrics */}
        <LiveMetricStrip realLand={realLand} chain={chain} />

        {/* 3D Scene Viewer */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Box size={18} color="var(--color-primary)" /> شبیه‌ساز سه‌بعدی ماژول‌ها
            </h2>
            {sceneOpen && (
              <Button variant="ghost" onClick={() => setSceneOpen(false)} icon={<X size={14} />}>بستن</Button>
            )}
          </div>
          {sceneOpen ? (
            <React.Suspense fallback={<div style={{ height: 420, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-secondary)' }}>در حال بارگذاری صحنه سه‌بعدی…</div>}>
              <DashboardScene3D mode={sceneMode} realLand={realLand} chain={chain} height={420} />
            </React.Suspense>
          ) : (
            <div style={{ padding: '0.8rem 1rem', borderRadius: 'var(--radius-lg)', background: 'var(--color-surface)', border: '1px dashed var(--color-border)', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
              برای باز کردن شبیه‌ساز سه‌بعدی هر ماژول، دکمه «سه‌بعدی» کنار عنوان ماژول را بزنید — صحنه با داده واقعی زنجیره (پارتو، عمق سیلاب، استخرهای کربن، عملکرد محصول) تغذیه می‌شود.
            </div>
          )}
        </div>

        {/* Modules: charts + many fields + 3D per module */}
        <HydromaModules realLand={realLand} chain={chain} onView3D={open3D} />

        {/* MRV carbon budget (Phase 4) */}
        <MrvCard lat={coords.lat} lon={coords.lon} />

        {/* Lab data vs model (Phase 4-D) */}
        <LabCompareCard lat={coords.lat} lon={coords.lon} />

        {/* Economy / livelihood (Phase 5) */}
        <EconomyCard lat={coords.lat} lon={coords.lon} />`r`n`r`n        {/* Real Supabase landscapes (Phase 6-B) */}`r`n        <SupabaseMapCard lat={coords.lat} lon={coords.lon} />`r`n`r`n        {/* Marketplace catalog on Supabase (Phase 6-B) */}`r`n        <MarketplaceCard />`r`n`r`n        {/* LMS (Phase 6-C) */}`r`n        <LmsCard />`r`n`r`n        {/* Audit & credits (Phase 7) */}`r`n        <AuditCard />`r`n`r`n        {/* Profile & Admin (Phase 8-A) */}`r`n        <ProfileCard />`r`n        <AdminCard />

        {/* Quick actions */}
        <div className="card" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center', marginTop: '1.5rem' }}>
          <Link to="/simulator"><Button variant="primary">مرکز شبیه‌سازهای علمی</Button></Link>
          <Link to="/virtual-lab"><Button variant="secondary">آزمایشگاه مجازی زمین</Button></Link>
        </div>
      </main>
    </div>
  );
};
