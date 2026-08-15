"use client";
import { useState, useEffect } from 'react';
import Navbar from '../../../components/layout/Navbar';
import Footer from '../../../components/layout/Footer';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { useAuth } from '../../../lib/auth-context';
import { useFarm } from '../../../lib/farm-context';
import { api } from '../../../lib/api-client';
import { motion } from 'framer-motion';
import {
  BarChart3, TrendingUp, Leaf, Satellite, Mountain,
  TreePine, Wallet, Activity, Clock, Award, Droplet
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';

export default function AnalyticsPage() {
  const { t, direction, language } = useI18n();
  const { colors } = useTheme();
  const { isAuthenticated } = useAuth();
  const { selectedFarm } = useFarm();
  const currentLang = language === 'fa' ? 'fa' : 'en';

  const [overview, setOverview] = useState<any>(null);
  const [soilTrends, setSoilTrends] = useState<any>(null);
  const [ndviTrends, setNdviTrends] = useState<any>(null);
  const [scenarioImpact, setScenarioImpact] = useState<any>(null);
  const [carbonSummary, setCarbonSummary] = useState<any>(null);
  const [timeline, setTimeline] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(365);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) loadAll();
    else setLoading(false);
  }, [isAuthenticated, days, selectedFarm]);

  const loadAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, st, nd, sc, ca, tl, mt] = await Promise.all([
        api.get<any>('/api/v1/analytics/overview').catch(() => ({ success: false, error: 'Failed' })),
        api.get<any>(`/api/v1/analytics/soil-trends?days=${days}${selectedFarm ? `&farm_id=${selectedFarm.id}` : ''}`).catch(() => ({ success: false })),
        api.get<any>(`/api/v1/analytics/ndvi-trends?days=${days}${selectedFarm ? `&farm_id=${selectedFarm.id}` : ''}`).catch(() => ({ success: false })),
        api.get<any>('/api/v1/analytics/scenario-impact').catch(() => ({ success: false })),
        api.get<any>('/api/v1/analytics/carbon-summary').catch(() => ({ success: false })),
        api.get<any>('/api/v1/analytics/activity-timeline?limit=30').catch(() => ({ success: false })),
        api.get<any>('/api/v1/analytics/performance-metrics').catch(() => ({ success: false })),
      ]);
      if (ov.success && ov.data) setOverview(ov.data);
      if (st.success && st.data) setSoilTrends(st.data);
      if (nd.success && nd.data) setNdviTrends(nd.data);
      if (sc.success && sc.data) setScenarioImpact(sc.data);
      if (ca.success && ca.data) setCarbonSummary(ca.data);
      if (tl.success && tl.data) setTimeline(tl.data);
      if (mt.success && mt.data) setMetrics(mt.data);
    } catch (e) {
      setError(String(e));
    }
    setLoading(false);
  };

  if (!isAuthenticated) {
    return (
      <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
        <Navbar />
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '80px 20px', textAlign: 'center' }}>
          <BarChart3 size={64} color={colors.textMuted} style={{ marginBottom: '16px', opacity: 0.3 }} />
          <h2 style={{ color: colors.text }}>
            {currentLang === 'fa' ? 'لطفاً وارد شوید' : 'Please Login'}
          </h2>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <Navbar />
      <div style={{ maxWidth: '1500px', margin: '0 auto', padding: '32px 20px' }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899)`,
            padding: '40px', borderRadius: '24px', color: 'white', marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <BarChart3 size={40} />
              <div>
                <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>
                  {currentLang === 'fa' ? 'تحلیل‌های پیشرفته' : 'Advanced Analytics'}
                </h1>
                <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                  {currentLang === 'fa' ? 'داشبورد یکپارچه' : 'Unified dashboard'}
                </p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              {[30, 90, 180, 365].map(d => (
                <button key={d} onClick={() => setDays(d)}
                  style={{
                    padding: '8px 16px', borderRadius: '8px',
                    background: days === d ? 'rgba(255,255,255,0.2)' : 'transparent',
                    color: 'white', border: '1px solid rgba(255,255,255,0.3)',
                    cursor: 'pointer', fontSize: '0.85rem', fontWeight: '600', fontFamily: 'inherit',
                  }}
                >{d}d</button>
              ))}
            </div>
          </div>
        </motion.div>

        {error && (
          <div style={{ padding: '16px', background: `${colors.danger}15`, borderRadius: '12px', marginBottom: '20px', color: colors.danger }}>
            ⚠️ {error}
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: colors.textMuted }}>Loading...</div>
        ) : (
          <>
            {/* Overview Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '32px' }}>
              {[
                { icon: TreePine, label: currentLang === 'fa' ? 'مزارع' : 'Farms', value: overview?.farms_count || 0, color: '#10b981' },
                { icon: Leaf, label: currentLang === 'fa' ? 'تحلیل خاک' : 'Soil Tests', value: overview?.soil_analyses_count || 0, color: '#f59e0b' },
                { icon: Satellite, label: currentLang === 'fa' ? 'سنجش از دور' : 'Satellite', value: overview?.satellite_analyses_count || 0, color: '#3b82f6' },
                { icon: TrendingUp, label: currentLang === 'fa' ? 'سناریوها' : 'Scenarios', value: overview?.scenario_runs_count || 0, color: '#8b5cf6' },
                { icon: Award, label: currentLang === 'fa' ? 'کربن' : 'Carbon', value: overview?.carbon_projects_count || 0, color: '#ec4899' },
              ].map((stat, i) => {
                const Icon = stat.icon;
                return (
                  <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                    style={{ padding: '20px', borderRadius: '16px', background: colors.cardBg, border: `1px solid ${colors.border}` }}>
                    <Icon size={24} color={stat.color} style={{ marginBottom: '12px' }} />
                    <div style={{ fontSize: '0.8rem', color: colors.textMuted }}>{stat.label}</div>
                    <div style={{ fontSize: '2rem', fontWeight: '800', color: stat.color }}>{stat.value}</div>
                  </motion.div>
                );
              })}
            </div>

            {/* Soil + NDVI Trends */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
              <div style={{ background: colors.cardBg, padding: '24px', borderRadius: '20px', border: `1px solid ${colors.border}` }}>
                <h3 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Leaf size={20} color="#10b981" />
                  {currentLang === 'fa' ? 'روند سلامت خاک' : 'Soil Health Trends'}
                </h3>
                {soilTrends?.data?.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={soilTrends.data}>
                      <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                      <XAxis dataKey="date" stroke={colors.textMuted} fontSize={10} />
                      <YAxis stroke={colors.textMuted} />
                      <Tooltip />
                      <Area type="monotone" dataKey="health_score" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : <div style={{ height: 250, display: 'flex', alignItems: 'center', justifyContent: 'center', color: colors.textMuted }}>No data</div>}
              </div>

              <div style={{ background: colors.cardBg, padding: '24px', borderRadius: '20px', border: `1px solid ${colors.border}` }}>
                <h3 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Satellite size={20} color="#3b82f6" />
                  {currentLang === 'fa' ? 'روند NDVI' : 'NDVI Trends'}
                </h3>
                {ndviTrends?.data?.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={ndviTrends.data}>
                      <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                      <XAxis dataKey="date" stroke={colors.textMuted} fontSize={10} />
                      <YAxis stroke={colors.textMuted} domain={[0, 1]} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="ndvi" stroke="#10b981" strokeWidth={2} />
                      <Line type="monotone" dataKey="evi" stroke="#f59e0b" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : <div style={{ height: 250, display: 'flex', alignItems: 'center', justifyContent: 'center', color: colors.textMuted }}>No data</div>}
              </div>
            </div>

            {/* Activity Timeline */}
            <div style={{ background: colors.cardBg, padding: '24px', borderRadius: '20px', border: `1px solid ${colors.border}` }}>
              <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Clock size={20} color={colors.accent} />
                {currentLang === 'fa' ? 'جدول زمانی فعالیت‌ها' : 'Activity Timeline'}
              </h3>
              {timeline?.activities?.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '500px', overflowY: 'auto' }}>
                  {timeline.activities.map((a, i) => (
                    <div key={i} style={{
                      padding: '14px', background: colors.bg, borderRadius: '10px',
                      display: 'flex', alignItems: 'center', gap: '14px', border: `1px solid ${colors.border}`,
                    }}>
                      <div style={{ fontSize: '1.8rem' }}>{a.icon}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '0.9rem', fontWeight: '600', color: colors.text }}>{a.title}</div>
                        <div style={{ fontSize: '0.8rem', color: colors.textMuted }}>{a.detail}</div>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                        {new Date(a.date).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              ) : <div style={{ textAlign: 'center', padding: '40px', color: colors.textMuted }}>No activities yet</div>}
            </div>
          </>
        )}
      </div>
      <Footer />
    </div>
  );
}
