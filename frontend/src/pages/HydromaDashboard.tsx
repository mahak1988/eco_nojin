import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Droplets, Waves, CloudRain, Wind, Leaf, LogOut, User, Sprout, Thermometer } from 'lucide-react';
import { AnimatedLogo } from '../components/branding/AnimatedLogo';
import { StatCard } from '../components/ui/StatCard';
import { Button } from '../components/ui/Button';
import { useAuth } from '../context/AuthContext';
import { toggleTheme } from '../hooks/useThemeMode';
import { RealLandSummaryCard } from '../components/hydroma/RealLandSummaryCard';
import { ScientificChainPanel } from '../components/hydroma/ScientificChainPanel';
import type { RealLandResult } from '../types/vll';
import {
  WaterBudgetChart, CarbonForecastChart, ErosionRiskMap, LivestockEconomicsChart } from '../components/simulators';

export const HydromaDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [realLand, setRealLand] = useState<RealLandResult | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lon: number }>({ lat: 35.5, lon: 51.5 });

  const soil = realLand?.soil;
  const climate = realLand?.climate;
  const rainfall = climate?.annual_rainfall_mm;
  const temp = climate?.avg_temp_c;
  const socPct = soil?.soc_g_kg != null ? (soil.soc_g_kg / 10).toFixed(2) : null;

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
      <section style={{ position: 'relative', padding: '3.5rem 2rem 5rem', overflow: 'hidden', textAlign: 'center' }}>
        <div className="hydroma-waves" />
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ position: 'relative', zIndex: 1 }}>
          <motion.div animate={{ y: [0, -8, 0] }} transition={{ repeat: Infinity, duration: 4 }} style={{ display: 'inline-flex', color: '#7dd3fc', marginBottom: '1rem' }}>
            <Waves size={44} />
          </motion.div>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: '#fff', marginBottom: '0.6rem' }}>
            خوش آمدی، {user?.name}
          </h1>
          <p style={{ color: '#bae6fd', fontSize: '1.05rem' }}>داشبورد هیدرولوژیک HyDroMa — آب، خاک، اقلیم</p>
        </motion.div>
      </section>

      <main style={{ maxWidth: 1400, margin: '-2rem auto 0', padding: '0 2rem 4rem', position: 'relative', zIndex: 2 }}>
        {/* Real data + scientific chain */}
        <div className="grid grid-cols-2" style={{ marginBottom: '2rem', alignItems: 'start' }}>
          <RealLandSummaryCard onLoaded={setRealLand} onCoordsChange={(lat: number, lon: number) => setCoords({ lat, lon })} />
          <ScientificChainPanel lat={coords.lat} lon={coords.lon} />
        </div>

        {/* Water stats — real values when loaded */}
        <div className="grid grid-cols-4" style={{ marginBottom: '2rem' }}>
          <StatCard title="بارش سالانه" value={rainfall != null ? `${rainfall.toFixed(1)} mm` : '—'} icon={<CloudRain size={24} />} color="info" />
          <StatCard title="دمای میانگین" value={temp != null ? `${temp.toFixed(1)} °C` : '—'} icon={<Thermometer size={24} />} color="warning" />
          <StatCard title="کربن آلی خاک (SOC)" value={socPct ? `${socPct}٪` : '—'} icon={<Sprout size={24} />} color="success" />
          <StatCard title="بافت خاک" value={soil?.texture ?? '—'} icon={<Droplets size={24} />} color="primary" />
        </div>

        {/* Charts — visualization demos (sample inputs; wired to real data in Phase 3) */}
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', margin: '0 0 0.75rem' }}>
          ⚠️ چارت‌های زیر نمونه‌های نمایشی با ورودی ثابت هستند — در فاز ۳ به داده واقعی زنجیره متصل می‌شوند.
        </p>
        <div className="grid grid-cols-2" style={{ marginBottom: '2rem' }}>
          <div className="card"><WaterBudgetChart /></div>
          <div className="card"><CarbonForecastChart years={20} initialSOC={1.5} /></div>
          <div className="card"><ErosionRiskMap windErosion={{ erosionTonHaYear: 15, riskLevel: 'high' }} waterErosion={{ soilLossTonHaYear: 8, riskLevel: 'high' }} /></div>
          <div className="card"><LivestockEconomicsChart herds={[
            { animalType: 'گاو', headCount: 20, revenue: 25000, feedCost: 8000, vetCost: 1000, laborCost: 3000, netProfit: 13000 },
            { animalType: 'گوسفند', headCount: 100, revenue: 18000, feedCost: 5000, vetCost: 1500, laborCost: 2000, netProfit: 9500 },
          ]} /></div>
        </div>

        {/* Quick actions */}
        <div className="card" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <Link to="/simulator"><Button variant="primary" icon={<Leaf size={16} />}>شبیه‌ساز کامل</Button></Link>
          <Link to="/pricing"><Button variant="secondary" icon={<Wind size={16} />}>ارتقای طرح</Button></Link>
        </div>
      </main>
    </div>
  );
};
