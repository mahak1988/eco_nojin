"use client";
import { useState, useEffect } from 'react';
import Footer from '../../../components/layout/Footer';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { useAuth } from '../../../lib/auth-context';
import { api } from '../../../lib/api-client';
import { motion } from 'framer-motion';
import {
  TreePine, Calculator, Atom, Wind, Droplet, Award,
  Leaf, FlaskConical, TrendingUp, Zap, Send, Info,
  BarChart3, Activity, Cpu, Beaker
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

export default function CarbonPage() {
  const { t, direction, locale: language } = useI18n();
  const { colors } = useTheme();
  const { isAuthenticated } = useAuth();
  const currentLang = t('car_en');

  const [formData, setFormData] = useState({
    name: 'My Forest Project',
    area_hectares: 10,
    species: 'tropical_moist',
    trees_per_ha: 1000,
    avg_diameter_cm: 20,
    avg_height_m: 12,
    project_years: 30,
    soil_carbon_tha: 40,
    mean_temperature_C: 25,
    latitude: 35.6892,
    longitude: 51.3890,
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [species, setSpecies] = useState<Record<string, number>>({});
  const [standards, setStandards] = useState<Record<string, any>>({});
  const [activeSection, setActiveSection] = useState<'overview' | 'photosynthesis' | 'quantum' | 'soil' | 'cooling' | 'verification'>('overview');

  useEffect(() => {
    loadMetadata();
  }, []);

  const loadMetadata = async () => {
    const [sp, st] = await Promise.all([
      api.get<any>('/api/v1/carbon/species'),
      api.get<any>('/api/v1/carbon/standards'),
    ]);
    if (sp.success && sp.data) setSpecies(sp.data);
    if (st.success && st.data) setStandards(st.data);
  };

  const calculate = async () => {
    setLoading(true);
    setError(null);
    const res = await api.post<any>('/api/v1/carbon/calculate', formData);
    if (res.success) setResult(res.data);
    else setError(res.error || 'Calculation failed');
    setLoading(false);
  };

  const registerProject = async () => {
    if (!isAuthenticated) {
      alert('Please login to register a project');
      return;
    }
    setLoading(true);
    const res = await api.post<any>('/api/v1/carbon/register', formData);
    if (res.success) {
      alert(`✅ Project registered! ID: ${res.data.project_id}\nCredits: ${res.data.credits.toFixed(2)} tCO₂`);
    } else {
      alert('Error: ' + (res.error || 'Registration failed'));
    }
    setLoading(false);
  };

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <div style={{ maxWidth: '1500px', margin: '0 auto', padding: '32px 20px' }}>
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{
            background: `linear-gradient(135deg, #0d9488, #10b981, #059669)`,
            padding: '40px', borderRadius: '24px', color: 'white',
            marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <TreePine size={40} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>
                {t('car_scientific_carbon_sequestration')}
              </h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                {t('car_precise_scientific_calculations_usin')}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Scientific Standards Banner */}
        <motion.div
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          style={{
            padding: '16px 20px', marginBottom: '24px',
            background: `${colors.accent}10`,
            border: `1px solid ${colors.accent}30`,
            borderRadius: '12px',
            display: 'flex', gap: '16px', alignItems: 'center',
          }}
        >
          <Info size={20} color={colors.accent} />
          <div style={{ fontSize: '0.85rem', color: colors.text }}>
            <strong>{t('car_supported_standards')}</strong>
            {' '}IPCC 2006 • Verra VM0047/VM0042 • Gold Standard • ISO 14064-2 • Plan Vivo
          </div>
        </motion.div>

        <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '24px' }}>
          {/* LEFT: Input Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
            style={{
              background: colors.cardBg, padding: '24px', borderRadius: '20px',
              border: `1px solid ${colors.border}`,
              position: 'sticky', top: '100px', alignSelf: 'flex-start',
            }}
          >
            <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calculator size={20} color={colors.success} />
              {t('car_project_parameters')}
            </h3>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ fontSize: '0.8rem', color: colors.textMuted, display: 'block', marginBottom: '4px' }}>
                {t('car_project_name')}
              </label>
              <input aria-label={t('car_project_name')} value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                style={{
                  width: '100%', padding: '10px', borderRadius: '8px',
                  border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text,
                }}
              />
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ fontSize: '0.8rem', color: colors.textMuted, display: 'block', marginBottom: '4px' }}>
                {t('car_tree_species')}
              </label>
              <select value={formData.species}
                onChange={(e) => setFormData({ ...formData, species: e.target.value })}
                style={{
                  width: '100%', padding: '10px', borderRadius: '8px',
                  border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text,
                }}
              >
                {Object.entries(species).map(([key, density]) => (
                  <option key={key} value={key}>
                    {key.replace(/_/g, ' ')} (ρ={density} g/cm³)
                  </option>
                ))}
              </select>
            </div>

            {Object.entries({
              area_hectares: { label: t('car_area_ha'), min: 0.1, max: 10000, step: 0.1 },
              trees_per_ha: { label: t('car_trees_ha'), min: 100, max: 10000, step: 50 },
              avg_diameter_cm: { label: t('car_avg_diameter_cm'), min: 1, max: 200, step: 1 },
              avg_height_m: { label: t('car_avg_height_m'), min: 1, max: 100, step: 0.5 },
              project_years: { label: t('car_project_years'), min: 5, max: 100, step: 1 },
              soil_carbon_tha: { label: t('car_initial_soil_c_t_ha'), min: 0, max: 200, step: 1 },
              mean_temperature_C: { label: t('car_mean_temp_c'), min: -10, max: 45, step: 0.5 },
            }).map(([key, cfg]: any) => (
              <div key={key} style={{ marginBottom: '14px' }}>
                <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: colors.textMuted, marginBottom: '4px' }}>
                  <span>{cfg.label}</span>
                  <span style={{ color: colors.success, fontWeight: '600' }}>
                    {(formData as any)[key]}
                  </span>
                </label>
                <input type="range" aria-label={cfg.label} min={cfg.min} max={cfg.max} step={cfg.step}
                  value={(formData as any)[key]}
                  onChange={(e) => setFormData({ ...formData, [key]: parseFloat(e.target.value) })}
                  style={{ width: '100%' }}
                />
              </div>
            ))}

            <motion.button
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              onClick={calculate} disabled={loading}
              style={{
                width: '100%', padding: '14px', marginTop: '8px',
                background: `linear-gradient(135deg, ${colors.success}, ${colors.accent})`,
                color: 'white', border: 'none', borderRadius: '10px',
                fontWeight: '600', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              }}
            >
              <Send size={18} />
              {loading ? 'Calculating...' : (t('car_scientific_calculation'))}
            </motion.button>

            {isAuthenticated && result && (
              <motion.button
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                onClick={registerProject}
                style={{
                  width: '100%', padding: '14px', marginTop: '8px',
                  background: colors.primary,
                  color: 'white', border: 'none', borderRadius: '10px',
                  fontWeight: '600', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                }}
              >
                <Award size={18} />
                {t('car_register_carbon_project')}
              </motion.button>
            )}

            {error && (
              <div style={{ marginTop: '12px', padding: '10px', background: `${colors.danger}15`, borderRadius: '8px', color: colors.danger, fontSize: '0.85rem' }}>
                {error}
              </div>
            )}
          </motion.div>

          {/* RIGHT: Results */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {!result ? (
              <div style={{
                background: colors.cardBg, padding: '80px 24px', borderRadius: '20px',
                border: `1px solid ${colors.border}`, textAlign: 'center', color: colors.textMuted,
              }}>
                <TreePine size={48} style={{ marginBottom: '16px', opacity: 0.3 }} />
                <p>{t('car_set_parameters_and_calculate')}</p>
              </div>
            ) : (
              <>
                {/* Overview Stats */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                  <StatCard icon={TreePine} label={t('car_total_trees')} value={result.project_summary.project_total.total_trees.toLocaleString()} color="#10b981" />
                  <StatCard icon={Leaf} label={t('car_total_co_t')} value={result.project_summary.project_total.total_co2_tons.toFixed(1)} color="#059669" />
                  <StatCard icon={Award} label={t('car_carbon_credits')} value={Math.round(result.project_summary.project_total.carbon_credits).toLocaleString()} color="#f59e0b" />
                  <StatCard icon={Wind} label={t('car_o_produced_t')} value={result.project_summary.project_total.oxygen_produced_tons.toFixed(1)} color="#06b6d4" />
                </div>

                {/* Section Tabs */}
                <div style={{
                  display: 'flex', gap: '8px', flexWrap: 'wrap',
                  background: colors.cardBg, padding: '12px', borderRadius: '16px',
                  border: `1px solid ${colors.border}`,
                }}>
                  {[
                    { key: 'overview', icon: BarChart3, label: t('car_overview') },
                    { key: 'photosynthesis', icon: Leaf, label: t('car_photosynthesis') },
                    { key: 'quantum', icon: Atom, label: t('car_quantum') },
                    { key: 'soil', icon: FlaskConical, label: t('car_soil_carbon') },
                    { key: 'cooling', icon: Droplet, label: t('car_cooling') },
                    { key: 'verification', icon: Award, label: t('car_verification') },
                  ].map((tab: any) => {
                    const Icon = tab.icon;
                    return (
                      <button key={tab.key} onClick={() => setActiveSection(tab.key)}
                        style={{
                          padding: '10px 16px', borderRadius: '10px',
                          background: activeSection === tab.key ? `${colors.success}20` : 'transparent',
                          color: activeSection === tab.key ? colors.success : colors.textMuted,
                          border: activeSection === tab.key ? `1px solid ${colors.success}40` : '1px solid transparent',
                          cursor: 'pointer', fontSize: '0.85rem', fontWeight: '600',
                          display: 'flex', alignItems: 'center', gap: '6px',
                          fontFamily: 'inherit',
                        }}
                      >
                        <Icon size={16} /> {tab.label}
                      </button>
                    );
                  })}
                </div>

                {/* Overview Section */}
                {activeSection === 'overview' && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    style={{ background: colors.cardBg, padding: '24px', borderRadius: '20px', border: `1px solid ${colors.border}` }}>
                    <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <BarChart3 size={20} color={colors.success} />
                      {t('car_project_summary')}
                    </h3>

                    {/* Per-tree stats */}
                    <div style={{
                      padding: '16px', background: `${colors.success}10`, borderRadius: '12px', marginBottom: '16px',
                    }}>
                      <h4 style={{ color: colors.success, marginBottom: '12px' }}>
                        {t('car_per_tree')}
                      </h4>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', fontSize: '0.9rem' }}>
                        <div><strong>{t('car_biomass')}</strong> {result.project_summary.per_tree.total_biomass_kg} kg</div>
                        <div><strong>{t('car_carbon')}</strong> {result.project_summary.per_tree.carbon_kg} kg</div>
                        <div><strong>CO₂:</strong> {result.project_summary.per_tree.co2_sequestered_kg} kg</div>
                        <div><strong>{t('car_wood_density')}</strong> {result.project_summary.wood_density_g_cm3} g/cm³</div>
                      </div>
                    </div>

                    {/* Allometry equation */}
                    <div style={{
                      padding: '16px', background: colors.bg, borderRadius: '12px', marginBottom: '16px',
                      fontFamily: 'monospace', fontSize: '0.9rem', color: colors.text,
                    }}>
                      <strong>Chave et al. 2014 (Nature):</strong>
                      <br />
                      AGB = 0.0673 × (ρ × D² × H)<sup>0.976</sup>
                      <br />
                      <span style={{ color: colors.textMuted, fontSize: '0.8rem' }}>
                        where ρ = wood density, D = DBH (cm), H = height (m)
                      </span>
                    </div>

                    {/* Timeline Chart */}
                    <div style={{ marginTop: '20px' }}>
                      <h4 style={{ color: colors.text, marginBottom: '12px' }}>
                        {t('car_soil_carbon_dynamics_over_time')}
                      </h4>
                      <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={result.soil_carbon.history_sample}>
                          <defs>
                            <linearGradient id="cGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                          <XAxis dataKey="year" stroke={colors.textMuted} />
                          <YAxis stroke={colors.textMuted} label={{ value: 't C/ha', angle: -90, position: 'insideLeft', fill: colors.textMuted }} />
                          <Tooltip contentStyle={{ background: colors.bgAlt, border: `1px solid ${colors.border}`, borderRadius: '8px' }} />
                          <Legend />
                          <Area type="monotone" dataKey="total_C_tha" stroke="#10b981" fillOpacity={1} fill="url(#cGrad)" name="Total Carbon" />
                          <Area type="monotone" dataKey="HUM" stroke="#8b5cf6" fillOpacity={0.3} name="HUM (stable)" />
                          <Area type="monotone" dataKey="BIO" stroke="#06b6d4" fillOpacity={0.3} name="BIO" />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </motion.div>
                )}

                {/* Photosynthesis Section */}
                {activeSection === 'photosynthesis' && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    style={{ background: colors.cardBg, padding: '24px', borderRadius: '20px', border: `1px solid ${colors.border}` }}>
                    <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Leaf size={20} color={colors.success} />
                      {t('car_farquhar_von_caemmerer_berry_photosy')}
                    </h3>

                    {/* Equations */}
                    <div style={{
                      padding: '20px', background: colors.bg, borderRadius: '12px', marginBottom: '20px',
                      fontFamily: 'monospace', fontSize: '0.9rem', color: colors.text, lineHeight: '1.8',
                    }}>
                      <strong>{t('car_biochemical_equations')}</strong>
                      <br />A = min(W<sub>c</sub>, W<sub>j</sub>) − R<sub>d</sub>
                      <br />W<sub>c</sub> = V<sub>cmax</sub> × (C<sub>i</sub> − Γ*) / (C<sub>i</sub> + K<sub>c</sub>(1 + O/K<sub>o</sub>))
                      <br />W<sub>j</sub> = J × (C<sub>i</sub> − Γ*) / (4C<sub>i</sub> + 8Γ*)
                      <br /><span style={{ color: colors.textMuted, fontSize: '0.8rem' }}>
                        where W<sub>c</sub>: Rubisco-limited, W<sub>j</sub>: RuBP-regeneration limited
                      </span>
                    </div>

                    {/* Results */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
                      {[
                        { label: 'Net Assimilation', value: `${result.photosynthesis.net_assimilation_umol} µmol`, sub: 'A', color: '#10b981' },
                        { label: 'Rubisco-limited', value: `${result.photosynthesis.rubisco_limited_Wc} µmol`, sub: 'Wc', color: '#f59e0b' },
                        { label: 'RuBP-limited', value: `${result.photosynthesis.RuBP_limited_Wj} µmol`, sub: 'Wj', color: '#3b82f6' },
                        { label: 'Electron Transport', value: `${result.photosynthesis.electron_transport_J} µmol`, sub: 'J', color: '#8b5cf6' },
                        { label: 'Quantum Yield', value: `${(result.photosynthesis.quantum_yield * 100).toFixed(2)}%`, sub: 'Φ', color: '#ec4899' },
                        { label: 'Daily CO₂', value: `${result.photosynthesis.daily_CO2_g_m2} g/m²`, sub: 'per day', color: '#06b6d4' },
                      ].map((stat, i) => (
                        <div key={i} style={{
                          padding: '14px', background: `${stat.color}10`,
                          border: `1px solid ${stat.color}30`, borderRadius: '10px',
                        }}>
                          <div style={{ fontSize: '0.75rem', color: colors.textMuted, marginBottom: '4px' }}>
                            {stat.label}
                          </div>
                          <div style={{ fontSize: '1.2rem', fontWeight: '800', color: stat.color }}>
                            {stat.value}
                          </div>
                          <div style={{ fontSize: '0.7rem', color: colors.textMuted, fontStyle: 'italic' }}>
                            {stat.sub}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Radar Chart */}
                    <div style={{ marginTop: '20px' }}>
                      <ResponsiveContainer width="100%" height={300}>
                        <RadarChart data={[
                          { subject: 'Wc', value: result.photosynthesis.rubisco_limited_Wc, fullMark: 150 },
                          { subject: 'Wj', value: result.photosynthesis.RuBP_limited_Wj, fullMark: 150 },
                          { subject: 'J', value: result.photosynthesis.electron_transport_J, fullMark: 200 },
                          { subject: 'A', value: result.photosynthesis.net_assimilation_umol, fullMark: 100 },
                          { subject: 'Rd', value: result.photosynthesis.dark_respiration_Rd, fullMark: 10 },
                        ]}>
                          <PolarGrid stroke={colors.border} />
                          <PolarAngleAxis dataKey="subject" stroke={colors.textMuted} />
                          <PolarRadiusAxis stroke={colors.border} />
                          <Radar name="FvCB Model" dataKey="value" stroke="#10b981" fill="#10b981" fillOpacity={0.6} />
                          <Tooltip contentStyle={{ background: colors.bgAlt, border: `1px solid ${colors.border}` }} />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  </motion.div>
                )}

                {/* Quantum Section */}
                {activeSection === 'quantum' && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    style={{ background: colors.cardBg, padding: '24px', borderRadius: '20px', border: `1px solid ${colors.border}` }}>
                    <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Atom size={20} color={colors.primary} />
                      {t('car_quantum_coherence_in_fmo_complex')}
                    </h3>

                    <div style={{
                      padding: '20px', background: `${colors.primary}10`, borderRadius: '12px',
                      marginBottom: '20px', border: `1px solid ${colors.primary}30`,
                    }}>
                      <p style={{ color: colors.text, lineHeight: '1.7', fontSize: '0.9rem' }}>
                        <strong>🔬 {t('car_amazing_discovery')}</strong>
                        <br />
                        {t('car_in_photosynthesis_the_fmo_fenna_matt')}
                      </p>
                    </div>

                    <div style={{
                      padding: '16px', background: colors.bg, borderRadius: '12px', marginBottom: '16px',
                      fontFamily: 'monospace', fontSize: '0.9rem', color: colors.text, lineHeight: '1.8',
                    }}>
                      <strong>{t('car_quantum_equations')}</strong>
                      <br />E<sub>photon</sub> = hc/λ (Planck-Einstein)
                      <br />Ψ(t) = Σ c<sub>i</sub>|i⟩ (Superposition)
                      <br />τ<sub>coherence</sub> ≈ 660 fs at 77K
                      <br />Efficiency<sub>quantum</sub> ≈ 99.99%
                      <br />Efficiency<sub>classical</sub> ≈ 70%
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
                      {[
                        { label: t('car_coherence_time'), value: `${result.quantum_efficiency.coherence_time_fs} fs`, icon: '⚛️', color: '#8b5cf6' },
                        { label: t('car_transfer_yield'), value: `${(result.quantum_efficiency.quantum_yield_transfer * 100).toFixed(4)}%`, icon: '✨', color: '#f59e0b' },
                        { label: t('car_quantum_advantage'), value: `+${result.quantum_efficiency.quantum_advantage_pct}%`, icon: '🚀', color: '#10b981' },
                        { label: t('car_absorption'), value: `${result.quantum_efficiency.peak_wavelength_nm} nm`, icon: '🌈', color: '#ef4444' },
                        { label: t('car_photon_energy'), value: `${result.quantum_efficiency.photon_energy_eV} eV`, icon: '⚡', color: '#3b82f6' },
                      ].map((stat, i) => (
                        <div key={i} style={{
                          padding: '14px', background: colors.bg,
                          border: `1px solid ${colors.border}`, borderRadius: '10px', textAlign: 'center',
                        }}>
                          <div style={{ fontSize: '1.8rem', marginBottom: '6px' }}>{stat.icon}</div>
                          <div style={{ fontSize: '0.75rem', color: colors.textMuted, marginBottom: '4px' }}>{stat.label}</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: '800', color: stat.color }}>{stat.value}</div>
                        </div>
                      ))}
                    </div>

                    <div style={{
                      marginTop: '20px', padding: '16px', background: `${colors.warm}10`,
                      borderRadius: '12px', border: `1px solid ${colors.warm}30`,
                      fontSize: '0.85rem', color: colors.text,
                    }}>
                      <strong>📚 {t('car_reference')}</strong>
                      <br />Engel, G. S., et al. (2007). "Evidence for wavelike energy transfer through quantum coherence in photosynthetic systems." <em>Nature</em>, 446, 782-786.
                    </div>
                  </motion.div>
                )}

                {/* Soil Carbon Section */}
                {activeSection === 'soil' && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    style={{ background: colors.cardBg, padding: '24px', borderRadius: '20px', border: `1px solid ${colors.border}` }}>
                    <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <FlaskConical size={20} color="#8b5cf6" />
                      {t('car_rothc_26_3_soil_carbon_model')}
                    </h3>

                    <div style={{
                      padding: '16px', background: colors.bg, borderRadius: '12px', marginBottom: '16px',
                      fontFamily: 'monospace', fontSize: '0.9rem', color: colors.text, lineHeight: '1.8',
                    }}>
                      <strong>{t('car_pool_dynamics_equations')}</strong>
                      <br />dC<sub>i</sub>/dt = I<sub>i</sub> − k<sub>i</sub> × r × C<sub>i</sub>
                      <br /><br />
                      <strong>Rate constants (yr⁻¹):</strong>
                      <br />• DPM: k = 10.0 (fast)
                      <br />• RPM: k = 0.3 (medium)
                      <br />• BIO: k = 0.66
                      <br />• HUM: k = 0.02 (slow, stable)
                      <br />• IOM: k = 0.0 (inert)
                    </div>

                    {/* Pool breakdown chart */}
                    <div style={{ marginTop: '20px' }}>
                      <h4 style={{ color: colors.text, marginBottom: '12px' }}>
                        {t('car_carbon_pool_distribution')}
                      </h4>
                      <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={[
                          { pool: 'DPM', value: result.soil_carbon.pools.DPM, color: '#f59e0b' },
                          { pool: 'RPM', value: result.soil_carbon.pools.RPM, color: '#f97316' },
                          { pool: 'BIO', value: result.soil_carbon.pools.BIO, color: '#06b6d4' },
                          { pool: 'HUM', value: result.soil_carbon.pools.HUM, color: '#8b5cf6' },
                          { pool: 'IOM', value: result.soil_carbon.pools.IOM, color: '#6b7280' },
                        ]}>
                          <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                          <XAxis dataKey="pool" stroke={colors.textMuted} />
                          <YAxis stroke={colors.textMuted} label={{ value: 't C/ha', angle: -90, position: 'insideLeft', fill: colors.textMuted }} />
                          <Tooltip contentStyle={{ background: colors.bgAlt, border: `1px solid ${colors.border}` }} />
                          <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                            {[
                              { color: '#f59e0b' }, { color: '#f97316' }, { color: '#06b6d4' },
                              { color: '#8b5cf6' }, { color: '#6b7280' },
                            ].map((entry, i) => <Cell key={i} fill={entry.color} />)}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '16px' }}>
                      <div style={{ padding: '14px', background: `${colors.success}10`, borderRadius: '10px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>{t('car_change')}</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: '800', color: colors.success }}>
                          {result.soil_carbon.change_tha > 0 ? '+' : ''}{result.soil_carbon.change_tha}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: colors.textMuted }}>t C/ha</div>
                      </div>
                      <div style={{ padding: '14px', background: `${colors.accent}10`, borderRadius: '10px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>{t('car_sequestration')}</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: '800', color: colors.accent }}>
                          {result.soil_carbon.sequestration_rate_tCO2_ha_yr}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: colors.textMuted }}>tCO₂/ha/yr</div>
                      </div>
                      <div style={{ padding: '14px', background: `${colors.primary}10`, borderRadius: '10px', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>{t('car_years_simulated')}</div>
                        <div style={{ fontSize: '1.4rem', fontWeight: '800', color: colors.primary }}>
                          {result.soil_carbon.years_simulated}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* Cooling Section */}
                {activeSection === 'cooling' && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    style={{ background: colors.cardBg, padding: '24px', borderRadius: '20px', border: `1px solid ${colors.border}` }}>
                    <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Droplet size={20} color="#06b6d4" />
                      {t('car_evapotranspiration_cooling_effect')}
                    </h3>

                    <div style={{
                      padding: '16px', background: colors.bg, borderRadius: '12px', marginBottom: '16px',
                      fontFamily: 'monospace', fontSize: '0.9rem', color: colors.text, lineHeight: '1.8',
                    }}>
                      <strong>{t('car_cooling_physics')}</strong>
                      <br />Q = m × L<sub>v</sub>
                      <br />L<sub>v</sub> = 2.45 MJ/kg (latent heat of vaporization)
                      <br />1 mm ET over 1 m² = 1 L water
                      <br />1 AC unit ≈ 3.5 kW cooling
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                      {[
                        { label: t('car_crown_area'), value: `${result.cooling_effect.total_crown_area_m2} m²`, icon: '🌳', color: '#10b981' },
                        { label: t('car_daily_et'), value: `${result.cooling_effect.water_transpired_liters_day} L`, icon: '💧', color: '#06b6d4' },
                        { label: t('car_cooling_energy'), value: `${result.cooling_effect.cooling_energy_MJ_day} MJ`, icon: '⚡', color: '#f59e0b' },
                        { label: 'kWh/day', value: `${result.cooling_effect.cooling_energy_kWh_day}`, icon: '🔋', color: '#8b5cf6' },
                        { label: t('car_ac_equivalent'), value: `${result.cooling_effect.equivalent_AC_units}`, icon: '❄️', color: '#3b82f6' },
                        { label: t('car_temp_drop'), value: `${result.cooling_effect.temperature_reduction_C}°C`, icon: '🌡️', color: '#ef4444' },
                      ].map((stat, i) => (
                        <div key={i} style={{
                          padding: '14px', background: `${stat.color}10`,
                          border: `1px solid ${stat.color}30`, borderRadius: '10px',
                          display: 'flex', alignItems: 'center', gap: '12px',
                        }}>
                          <div style={{ fontSize: '2rem' }}>{stat.icon}</div>
                          <div>
                            <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>{stat.label}</div>
                            <div style={{ fontSize: '1.3rem', fontWeight: '800', color: stat.color }}>{stat.value}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* Verification Section */}
                {activeSection === 'verification' && (
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    style={{ background: colors.cardBg, padding: '24px', borderRadius: '20px', border: `1px solid ${colors.border}` }}>
                    <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Award size={20} color="#f59e0b" />
                      {t('car_carbon_credit_verification')}
                    </h3>

                    <div style={{
                      padding: '16px', background: `${colors.warm}10`, borderRadius: '12px',
                      border: `1px solid ${colors.warm}30`, marginBottom: '20px',
                    }}>
                      <h4 style={{ color: colors.warm, marginBottom: '8px' }}>
                        {t('car_verification_result_verra_vm0047')}
                      </h4>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', fontSize: '0.9rem' }}>
                        <div><strong>{t('car_gross_credits')}</strong> {result.verification.gross_credits.toFixed(2)} tCO₂</div>
                        <div><strong>{t('car_uncertainty_deduction')}</strong> {result.verification.uncertainty_deduction_pct}%</div>
                        <div><strong>{t('car_buffer_pool')}</strong> {result.verification.buffer_pool_pct}%</div>
                        <div><strong>{t('car_net_credits')}</strong> <span style={{ color: colors.success, fontWeight: '800', fontSize: '1.1rem' }}>{result.verification.net_credits.toFixed(2)}</span></div>
                      </div>
                    </div>

                    <h4 style={{ color: colors.text, marginBottom: '12px' }}>
                      {t('car_available_standards')}
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {Object.entries(standards).map(([key, std]: any) => (
                        <div key={key} style={{
                          padding: '12px', background: colors.bg,
                          border: `1px solid ${colors.border}`, borderRadius: '8px',
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        }}>
                          <div>
                            <div style={{ fontWeight: '600', color: colors.text }}>{std.name}</div>
                            <div style={{ fontSize: '0.75rem', color: colors.textMuted, marginTop: '2px' }}>
                              Tier: {std.tier} • Permanence: {std.permanence_years}yr
                            </div>
                          </div>
                          <div style={{ fontSize: '0.85rem', color: colors.warm, fontWeight: '600' }}>
                            ±{std.uncertainty_pct}%
                          </div>
                        </div>
                      ))}
                    </div>

                    <div style={{
                      marginTop: '20px', padding: '14px', background: `${colors.success}10`,
                      borderRadius: '10px', fontSize: '0.85rem', color: colors.text,
                    }}>
                      <strong>📖 {t('car_references')}</strong>
                      <ul style={{ marginTop: '8px', paddingLeft: '20px', lineHeight: '1.8' }}>
                        {result.scientific_references?.map((ref: string, i: number) => (
                          <li key={i}>{ref}</li>
                        ))}
                      </ul>
                    </div>
                  </motion.div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }: any) {
  return (
    <motion.div whileHover={{ y: -4 }} style={{
      padding: '20px', borderRadius: '16px',
      background: `${color}10`,
      border: `2px solid ${color}40`,
      textAlign: 'center',
    }}>
      <Icon size={28} color={color} style={{ marginBottom: '8px' }} />
      <div style={{ fontSize: '0.8rem', color: 'rgba(0,0,0,0.6)', marginBottom: '4px' }}>{label}</div>
      <div style={{ fontSize: '1.5rem', fontWeight: '800', color }}>{value}</div>
    </motion.div>
  );
}
