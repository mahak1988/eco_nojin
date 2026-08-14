'use client';
import { useEffect } from 'react';
import LanguageSwitcher from '../components/LanguageSwitcher';
import SoilDashboard from '../components/SoilDashboard';
import SatellitePanel from '../components/SatellitePanel';
import ChatAssistant from '../components/ChatAssistant';
import MarketplacePanel from '../components/MarketplacePanel';
import ScenarioPanel from '../components/ScenarioPanel';
import CropPlannerPanel from '../components/CropPlannerPanel';
import CarbonCreditPanel from '../components/CarbonCreditPanel';
import WatershedPanel from '../components/WatershedPanel';
import BenchmarkPanel from '../components/BenchmarkPanel';
import MobileFeaturesPanel from '../components/MobileFeaturesPanel';
import { useI18n } from '../lib/i18n-context';
import { registerServiceWorker } from '../lib/swRegistration';

export default function Home() {
  const { t } = useI18n();

  useEffect(() => {
    registerServiceWorker();
  }, []);

  return (
    <main style={{ minHeight: '100vh', padding: 'clamp(16px, 4vw, 32px)', maxWidth: '1400px', margin: '0 auto', background: '#f8fafc' }}>
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '32px',
        borderBottom: '2px solid #e2e8f0',
        paddingBottom: '16px'
      }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#15803d', margin: 0 }}>
            🌍 Eco Nojin
          </h1>
          <p style={{ color: '#64748b', margin: '4px 0 0 0' }}>{t('tagline')}</p>
        </div>
        <LanguageSwitcher />
      </header>

      <section style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#1e293b' }}>
          {t('welcome')}
        </h2>
      </section>

      {/* All Panels */}
      <SoilDashboard />
      <SatellitePanel />
      <MobileFeaturesPanel />
      <CropPlannerPanel />
      <ScenarioPanel />
      <CarbonCreditPanel />
      <WatershedPanel />
      <MarketplacePanel />
      <BenchmarkPanel />
      <ChatAssistant />

      <footer style={{
        marginTop: '48px',
        paddingTop: '16px',
        borderTop: '1px solid #e2e8f0',
        textAlign: 'center',
        color: '#94a3b8',
        fontSize: '0.875rem'
      }}>
        <p>Eco Nojin Platform v1.1 | HyDroMa Engine | PWA + Offline-First</p>
        <p>14 Languages • 10 Backend Modules • Capacitor Ready</p>
      </footer>
    </main>
  );
}
