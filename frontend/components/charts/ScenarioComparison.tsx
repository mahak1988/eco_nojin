"use client";
import { useEffect, useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ComposedChart, Area,
} from 'recharts';
import { motion } from 'framer-motion';
import { TrendingUp, Thermometer, CloudRain, AlertTriangle } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';
import { useFarm } from '../../lib/farm-context';
import { api } from '../../lib/api-client';

const SSP_COLORS = {
  ssp126: '#10b981',
  ssp245: '#f59e0b',
  ssp370: '#ef4444',
  ssp585: '#7c2d12',
};

const SSP_LABELS = {
  ssp126: 'SSP1-2.6 (Best)',
  ssp245: 'SSP2-4.5 (Moderate)',
  ssp370: 'SSP3-7.0 (Bad)',
  ssp585: 'SSP5-8.5 (Worst)',
};

export default function ScenarioComparison({ baselineTemp = 18.5, baselinePrecip = 380 }) {
  const { colors } = useTheme();
  const { selectedFarm } = useFarm();
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    runAllScenarios();
  }, [selectedFarm]);

  const runAllScenarios = async () => {
    setLoading(true);
    const scenarios = ['ssp126', 'ssp245', 'ssp370', 'ssp585'];
    const results: any[] = [];

    for (const sc of scenarios) {
      const res = await api.post<any>('/api/v1/scenarios/apply', {
        baseline_temp: baselineTemp,
        baseline_precip: baselinePrecip,
        scenario: sc,
        year: 2050,
        farm_id: selectedFarm?.id,
      });
      if (res.success && res.data) {
        results.push({
          scenario: sc,
          label: SSP_LABELS[sc as keyof typeof SSP_LABELS],
          tempChange: res.data.temperature_change,
          precipChange: res.data.precipitation_change_percent,
          droughtRisk: res.data.drought_risk_index,
          projectedTemp: res.data.projected_temperature,
          projectedPrecip: res.data.projected_precipitation,
        });
      }
    }
    setData(results);
    setLoading(false);
  };

  const timelineData = [2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100].map(year => {
    const row: any = { year };
    ['ssp126', 'ssp245', 'ssp370', 'ssp585'].forEach(sc => {
      const sspData = {
        ssp126: { temp: 1.2, precip: -3 },
        ssp245: { temp: 2.2, precip: -8 },
        ssp370: { temp: 3.2, precip: -13 },
        ssp585: { temp: 4.0, precip: -18 },
      }[sc]!;
      const scale = Math.min((year - 2020) / 30, 1.5);
      row[`${sc}_temp`] = baselineTemp + sspData.temp * scale;
      row[`${sc}_precip`] = baselinePrecip * (1 + (sspData.precip / 100) * scale);
    });
    return row;
  });

  if (loading || data.length === 0) {
    return (
      <div style={{
        padding: '40px', textAlign: 'center', color: colors.textMuted,
        background: colors.cardBg, borderRadius: '20px',
        border: `1px solid ${colors.border}`,
      }}>
        Loading scenarios...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
        {data.map((d, i) => (
          <motion.div
            key={d.scenario}
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ y: -4 }}
            style={{
              padding: '16px', borderRadius: '14px',
              background: `${SSP_COLORS[d.scenario as keyof typeof SSP_COLORS]}15`,
              border: `2px solid ${SSP_COLORS[d.scenario as keyof typeof SSP_COLORS]}40`,
            }}
          >
            <div style={{ fontSize: '0.75rem', color: colors.textMuted, marginBottom: '4px' }}>
              {d.label}
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginBottom: '8px' }}>
              <Thermometer size={16} color={SSP_COLORS[d.scenario as keyof typeof SSP_COLORS]} />
              <span style={{ fontSize: '1.5rem', fontWeight: '800', color: SSP_COLORS[d.scenario as keyof typeof SSP_COLORS] }}>
                +{d.tempChange.toFixed(1)}آ°C
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: colors.textMuted }}>
              <span>ًںŒ§ï¸ڈ {d.precipChange.toFixed(1)}%</span>
              <span>ًں”¥ {(d.droughtRisk * 100).toFixed(0)}%</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Temperature Timeline */}
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{
          background: colors.cardBg, padding: '20px', borderRadius: '20px',
          border: `1px solid ${colors.border}`,
        }}
      >
        <h4 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={18} color={colors.primary} />
          Temperature Projection (2030-2100)
        </h4>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={timelineData}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
            <XAxis dataKey="year" stroke={colors.textMuted} />
            <YAxis stroke={colors.textMuted} unit="آ°C" />
            <Tooltip
              contentStyle={{ background: colors.bgAlt, border: `1px solid ${colors.border}`, borderRadius: '8px' }}
            />
            <Legend />
            {Object.entries(SSP_COLORS).map(([sc, color]) => (
              <Line key={sc} type="monotone" dataKey={`${sc}_temp`}
                name={SSP_LABELS[sc as keyof typeof SSP_LABELS]}
                stroke={color} strokeWidth={2} dot={{ r: 3 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Precipitation Comparison */}
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{
          background: colors.cardBg, padding: '20px', borderRadius: '20px',
          border: `1px solid ${colors.border}`,
        }}
      >
        <h4 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CloudRain size={18} color={colors.accent} />
          2050 Scenario Comparison
        </h4>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
            <XAxis dataKey="label" stroke={colors.textMuted} fontSize={11} />
            <YAxis yAxisId="left" stroke={colors.textMuted} unit="آ°C" />
            <YAxis yAxisId="right" orientation="right" stroke={colors.textMuted} unit="mm" />
            <Tooltip
              contentStyle={{ background: colors.bgAlt, border: `1px solid ${colors.border}`, borderRadius: '8px' }}
            />
            <Legend />
            <Bar yAxisId="left" dataKey="projectedTemp" fill={colors.primary}
              name="Temperature (آ°C)" radius={[8, 8, 0, 0]} />
            <Line yAxisId="right" type="monotone" dataKey="projectedPrecip"
              stroke={colors.accent} strokeWidth={3} name="Precipitation (mm)"
              dot={{ r: 6, fill: colors.accent }} />
          </ComposedChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Drought Risk Gauge */}
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{
          background: colors.cardBg, padding: '20px', borderRadius: '20px',
          border: `1px solid ${colors.border}`,
        }}
      >
        <h4 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={18} color={colors.warm} />
          Drought Risk Index
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {data.map(d => (
            <div key={d.scenario}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.85rem' }}>
                <span style={{ color: colors.text, fontWeight: '600' }}>{d.label}</span>
                <span style={{ color: SSP_COLORS[d.scenario as keyof typeof SSP_COLORS], fontWeight: '700' }}>
                  {(d.droughtRisk * 100).toFixed(0)}%
                </span>
              </div>
              <div style={{ height: '10px', background: colors.bg, borderRadius: '5px', overflow: 'hidden' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${d.droughtRisk * 100}%` }}
                  transition={{ duration: 1 }}
                  style={{
                    height: '100%',
                    background: `linear-gradient(90deg, ${colors.success}, ${colors.warm}, ${colors.danger})`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
