import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Leaf, Droplets, Wind, Beef, TrendingUp,
  Activity, Trees, Box,
} from 'lucide-react';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, StatCard, Tabs } from '../components/ui';
import { CropComparisonChart } from '../components/simulators/CropComparisonChart';
import { CarbonForecastChart } from '../components/simulators/CarbonForecastChart';
import { ErosionRiskMap } from '../components/simulators/ErosionRiskMap';
import { WaterBudgetChart } from '../components/simulators/WaterBudgetChart';
import { LivestockEconomicsChart } from '../components/simulators/LivestockEconomicsChart';
import { FarmScene3D } from '../components/3d/FarmScene3D';
import { simulatorService, type SimulationContext } from '../services/simulatorApi';

export const SimulatorDashboard: React.FC = () => {
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>({});

  // Default Context
  const [context] = useState<SimulationContext>({
    soil: {
      texture: 'loam',
      organicCarbonPct: 1.5,
      infiltrationRateMmHr: 20,
    },
    weather: {
      precipitationMm: 50,
      windSpeedMs: 12,
      tempMinC: 15,
      tempMaxC: 32,
      solarRadiationMjM2: 18,
    },
    crop: {
      cropType: 'wheat',
      plantingDate: '2026-10-15',
    },
    bbox: {
      north: 35.5,
      south: 35.4,
      east: 51.5,
      west: 51.4,
    },
  });

  // Run All Simulations
  const runAllSimulations = async () => {
    setLoading(true);
    try {
      const [crop, carbon, erosion, water] = await Promise.all([
        simulatorService.simulateCropGrowth(context),
        simulatorService.simulateCarbonSequestration(context),
        simulatorService.simulateErosion(context),
        simulatorService.analyzeWaterBudget(context),
      ]);

      setResults({ crop, carbon, erosion, water });
    } catch (error) {
      console.error('Simulation error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runAllSimulations();
  }, []);

  const tabs = [
    {
      id: 'overview',
      label: 'نمای کلی',
      icon: <Activity size={16} />,
      content: (
        <div>
          {/* Stats */}
          <div className="grid grid-cols-4" style={{ marginBottom: '2rem' }}>
            <StatCard
              title="کربن خاک"
              value={results.carbon?.summary?.final_soc_t_ha || '1.8'}
              change={12.5}
              icon={<Leaf size={24} />}
              color="primary"
            />
            <StatCard
              title="بازده آب"
              value="87%"
              change={5.2}
              icon={<Droplets size={24} />}
              color="info"
            />
            <StatCard
              title="ریسک فرسایش"
              value={results.erosion?.wind?.summary?.risk_level || 'کم'}
              change={-15}
              icon={<Wind size={24} />}
              color="success"
            />
            <StatCard
              title="عملکرد محصول"
              value={results.crop?.summary?.yield_ton_ha || '4.2'}
              change={8.3}
              icon={<TrendingUp size={24} />}
              color="accent"
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-2">
            <Card title="پیش‌بینی کربن" icon={<Leaf size={20} />}>
              <CarbonForecastChart years={20} initialSOC={1.5} managementScenario="conservation" />
            </Card>

            <Card title="بودجه آب" icon={<Droplets size={20} />}>
              <WaterBudgetChart
                precipitationMm={500}
                infiltrationMm={280}
                runoffMm={120}
                evapotranspirationMm={80}
                aquiferRechargeMm={20}
              />
            </Card>
          </div>
        </div>
      ),
    },
    {
      id: 'crops',
      label: 'برنامه کشت',
      icon: <Leaf size={16} />,
      content: (
        <Card title="مقایسه سناریوهای کشت" icon={<Leaf size={20} />}>
          <CropComparisonChart
            currentCrop={{ cropType: 'گندم', yieldTonHa: 4.2, waterMm: 450, revenue: 1680 }}
            alternativeCrop={{ cropType: 'زعفران', yieldTonHa: 0.01, waterMm: 280, revenue: 3500 }}
          />
        </Card>
      ),
    },
    {
      id: 'erosion',
      label: 'فرسایش',
      icon: <Wind size={16} />,
      content: (
        <div className="grid grid-cols-2">
          <Card title="تحلیل فرسایش" icon={<Wind size={20} />}>
            <ErosionRiskMap
              windErosion={results.erosion?.wind?.summary || { erosionTonHaYear: 25, riskLevel: 'severe' }}
              waterErosion={results.erosion?.water?.summary || { soilLossTonHaYear: 12, riskLevel: 'high' }}
              hasWindbreak={true}
              windbreakReduction={0.4}
            />
          </Card>

          <Card title="اثر بادشکن" icon={<Trees size={20} />}>
            <div style={{ padding: '1rem' }}>
              <h4>🌳 بادشکن Cypress</h4>
              <ul style={{ listStyle: 'none', lineHeight: 2 }}>
                <li>✅ فرسایش بادی <strong>۶۰٪ کاهش</strong></li>
                <li>✅ تبخیر سطحی <strong>۳۵٪ کاهش</strong></li>
                <li>✅ رطوبت خاک <strong>۱۵٪ افزایش</strong></li>
                <li>💰 هزینه: $۵,۰۰۰ / بازگشت: ۴ سال</li>
              </ul>
            </div>
          </Card>
        </div>
      ),
    },
    {
      id: 'water',
      label: 'بودجه آب',
      icon: <Droplets size={16} />,
      content: (
        <Card title="بودجه آب" icon={<Droplets size={20} />}>
          <WaterBudgetChart
            precipitationMm={500}
            infiltrationMm={280}
            runoffMm={120}
            evapotranspirationMm={80}
            aquiferRechargeMm={20}
          />
        </Card>
      ),
    },
    {
      id: 'livestock',
      label: 'دامداری',
      icon: <Beef size={16} />,
      content: (
        <Card title="اقتصاد گله" icon={<Beef size={20} />}>
          <LivestockEconomicsChart
            herds={[
              { animalType: 'گاو', headCount: 20, revenue: 25000, feedCost: 8000, vetCost: 1000, laborCost: 3000, netProfit: 13000 },
              { animalType: 'گوسفند', headCount: 100, revenue: 18000, feedCost: 5000, vetCost: 1500, laborCost: 2000, netProfit: 9500 },
              { animalType: 'مرغ', headCount: 500, revenue: 12000, feedCost: 7000, vetCost: 500, laborCost: 1500, netProfit: 3000 },
            ]}
          />
        </Card>
      ),
    },
    {
      id: '3d',
      label: 'سه‌بعدی',
      icon: <Box size={16} />,
      content: (
        <Card title="نمای سه‌بعدی مزرعه" icon={<Box size={20} />}>
          <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
            <button
              onClick={() => setViewMode('2d')}
              className={`btn ${viewMode === '2d' ? 'btn-primary' : 'btn-secondary'}`}
            >
              2D
            </button>
            <button
              onClick={() => setViewMode('3d')}
              className={`btn ${viewMode === '3d' ? 'btn-primary' : 'btn-secondary'}`}
            >
              3D
            </button>
          </div>
          
          {viewMode === '3d' ? (
            <FarmScene3D
              showTerrain={true}
              showCrops={true}
              cropType="wheat"
              growthStage={0.7}
              ndvi={0.75}
              herds={[
                { type: 'sheep', count: 20 },
                { type: 'goat', count: 10 },
              ]}
            />
          ) : (
            <div style={{ height: 400, background: 'var(--color-surface)', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <p>نمای 2D - نقشه ماهواره‌ای</p>
            </div>
          )}
        </Card>
      ),
    },
  ];

  return (
    <AppLayout>
      <div style={{ maxWidth: 1600, margin: '0 auto' }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ marginBottom: '2rem' }}
        >
          <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            شبیه‌ساز دیجیتال مزرعه
          </h1>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            تحلیل جامع و پیش‌بینی عملکرد مزرعه شما با HyDroMa
          </p>
        </motion.div>

        {/* Tabs */}
        <Tabs tabs={tabs} defaultTab="overview" variant="pills" />

        {/* Refresh Button */}
        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <button
            onClick={runAllSimulations}
            className="btn btn-primary"
            disabled={loading}
            style={{ padding: '1rem 2rem' }}
          >
            {loading ? 'در حال شبیه‌سازی...' : '🔄 اجرای مجدد شبیه‌سازی'}
          </button>
        </div>
      </div>
    </AppLayout>
  );
};
