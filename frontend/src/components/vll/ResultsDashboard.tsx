import React from 'react';
import { motion } from 'framer-motion';
import {
  Droplets,
  Leaf,
  Wind,
  DollarSign,
  TrendingUp,
  Sprout,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';
import { Card, StatCard, ProgressRing } from '../ui';
import { CarbonForecastChart } from '../simulators/CarbonForecastChart';
import { WaterBudgetChart } from '../simulators/WaterBudgetChart';
import type { SimulationResult } from '../../types/vll';

interface ResultsDashboardProps {
  result: SimulationResult | null;
  baseline?: SimulationResult;
}

export const ResultsDashboard: React.FC<ResultsDashboardProps> = ({ result, baseline }) => {
  if (!result) {
    return (
      <Card title="نتایج شبیه‌سازی" icon={<TrendingUp size={20} />}>
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>
          <Sprout size={64} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
          <p>ابتدا مداخلات را انتخاب و شبیه‌سازی را اجرا کنید</p>
        </div>
      </Card>
    );
  }

  const scoreColor =
    result.sustainabilityScore >= 75
      ? 'var(--color-success)'
      : result.sustainabilityScore >= 50
        ? 'var(--color-warning)'
        : 'var(--color-error)';

  const calculateChange = (current: number, baselineValue: number): number => {
    if (!baselineValue) return 0;
    return ((current - baselineValue) / baselineValue) * 100;
  };

  return (
    <div>
      {/* Sustainability Score Header */}
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        style={{
          background: `linear-gradient(135deg, ${scoreColor}20, ${scoreColor}05)`,
          border: `2px solid ${scoreColor}`,
          borderRadius: 'var(--radius-2xl)',
          padding: '2rem',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '2rem',
        }}
      >
        <ProgressRing
          value={result.sustainabilityScore}
          size={120}
          strokeWidth={10}
          color={scoreColor}
          label="نمره پایداری"
        />
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: '0 0 0.5rem 0' }}>
            {result.sustainabilityScore >= 75
              ? '✅ سناریو پایدار'
              : result.sustainabilityScore >= 50
                ? '⚠️ نیاز به بهبود'
                : '❌ سناریو بحرانی'}
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: '1rem' }}>
            {result.sustainabilityScore >= 75
              ? 'این سناریو از نظر اقتصادی، زیست‌محیطی و اجتماعی قابل قبول است.'
              : 'پیشنهاد می‌شود مداخلات بیشتری اعمال کنید.'}
          </p>
          {result.warnings.length > 0 && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                color: 'var(--color-warning)',
                fontSize: '0.875rem',
              }}
            >
              <AlertTriangle size={16} />
              {result.warnings.length} هشدار
            </div>
          )}
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4" style={{ marginBottom: '2rem' }}>
        <StatCard
          title="نفوذ آب"
          value={`${result.hydrology.infiltrationMm.toFixed(0)} mm`}
          change={
            baseline
              ? calculateChange(result.hydrology.infiltrationMm, baseline.hydrology.infiltrationMm)
              : undefined
          }
          icon={<Droplets size={24} />}
          color="info"
        />
        <StatCard
          title="فرسایش خاک"
          value={`${result.erosion.waterErosionTonHaYear.toFixed(1)} t/ha`}
          change={
            baseline
              ? calculateChange(
                  result.erosion.waterErosionTonHaYear,
                  baseline.erosion.waterErosionTonHaYear
                )
              : undefined
          }
          icon={<Wind size={24} />}
          color="warning"
        />
        <StatCard
          title="کربن ذخیره"
          value={`${result.carbon.totalSequestrationTonCO2Year.toFixed(1)} t`}
          change={
            baseline
              ? calculateChange(
                  result.carbon.totalSequestrationTonCO2Year,
                  baseline.carbon.totalSequestrationTonCO2Year
                )
              : undefined
          }
          icon={<Leaf size={24} />}
          color="success"
        />
        <StatCard
          title="سود خالص"
          value={`$${result.economics.netProfitUsd.toLocaleString()}`}
          change={
            baseline
              ? calculateChange(result.economics.netProfitUsd, baseline.economics.netProfitUsd)
              : undefined
          }
          icon={<DollarSign size={24} />}
          color="accent"
        />
      </div>

      {/* Detailed Charts */}
      <div className="grid grid-cols-2" style={{ marginBottom: '2rem' }}>
        <Card title="بودجه آب" icon={<Droplets size={20} />}>
          <WaterBudgetChart
            precipitationMm={result.hydrology.precipitationMm}
            infiltrationMm={result.hydrology.infiltrationMm}
            runoffMm={result.hydrology.runoffMm}
            evapotranspirationMm={result.hydrology.evapotranspirationMm}
            aquiferRechargeMm={result.hydrology.aquiferRechargeMm}
          />
        </Card>

        <Card title="ترسیب کربن (۲۰ ساله)" icon={<Leaf size={20} />}>
          <CarbonForecastChart
            years={20}
            initialSOC={result.carbon.soilCarbonTonHa}
            managementScenario="conservation"
          />
        </Card>
      </div>

      {/* AI Recommendations */}
      {result.recommendations.length > 0 && (
        <Card title="پیشنهادات هوشمند آگرو-مشاور" icon={<CheckCircle size={20} />}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {result.recommendations.map((rec, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                style={{
                  padding: '1rem',
                  background: 'var(--color-surface)',
                  borderRadius: 'var(--radius-lg)',
                  borderRight: '4px solid var(--color-primary)',
                  fontSize: '0.875rem',
                  lineHeight: 1.6,
                }}
              >
                💡 {rec}
              </motion.div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
