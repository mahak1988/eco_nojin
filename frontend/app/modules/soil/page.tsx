"use client";
import { useState, useEffect } from 'react';
import Footer from '../../../components/layout/Footer';
import SoilTriangle from '../../../components/visualizations/SoilTriangle';
import HealthGauge from '../../../components/visualizations/HealthGauge';
import NutrientMeter from '../../../components/visualizations/NutrientMeter';
import { useI18n } from '../../../lib/i18n-context';
import { useTheme } from '../../../lib/theme-context';
import { useAuth } from '../../../lib/auth-context';
import { useFarm } from '../../../lib/farm-context';
import { api } from '../../../lib/api-client';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Leaf, Beaker, Send, History, AlertCircle, CheckCircle2,
  AlertTriangle, Droplet, Shield, TrendingUp, Bug,
  ChevronDown, ChevronUp,
} from 'lucide-react';

import SoilDashboard from '../../../components/SoilDashboard';

export default function SoilPage() {
  const { t, direction, locale } = useI18n();
  const { colors } = useTheme();
  const { isAuthenticated } = useAuth();
  const { selectedFarm } = useFarm();

  const [formData, setFormData] = useState({
    pH: 6.8, organic_matter: 2.5,
    nitrogen: 45, phosphorus: 28, potassium: 180,
    clay: 25, silt: 45, sand: 30,
    drainage_issues: false,
    compaction_issues: false,
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'organic' | 'chemical' | 'biological'>('organic');
  const [expandedSolution, setExpandedSolution] = useState<string | null>(null);

  const FIELD_LABELS: Record<string, string> = {
    pH: 'pH',
    organic_matter: t('soil_field_organic_matter'),
    nitrogen: t('soil_field_nitrogen'),
    phosphorus: t('soil_field_phosphorus'),
    potassium: t('soil_field_potassium'),
    clay: t('soil_field_clay'),
    silt: t('soil_field_silt'),
    sand: t('soil_field_sand'),
  };

  useEffect(() => {
    if (selectedFarm) loadHistory();
  }, [selectedFarm]);

  const loadHistory = async () => {
    if (!selectedFarm) return;
    const res = await api.get<any>(`/api/v1/soil/history/${selectedFarm.id}`);
    if (res.success && res.data) setHistory(res.data.analyses || []);
  };

  const analyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    const res = await api.post<any>('/api/v1/soil/analyze', {
      ...formData,
      farm_id: selectedFarm?.id,
      language: locale,
    });

    if (res.success) {
      setResult(res.data);
      if (selectedFarm) loadHistory();
    } else {
      setError(res.error || t('soil_analyze_failed'));
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
            background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
            padding: '40px', borderRadius: '24px', color: 'white',
            marginBottom: '32px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Leaf size={40} />
            <div>
              <h1 style={{ fontSize: '2rem', fontWeight: '800', margin: 0 }}>
                {t('soil_title')}
              </h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                {t('soil_subtitle')}
              </p>
            </div>
          </div>
        </motion.div>

        <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '24px' }}>
          {/* LEFT: Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
            style={{
              background: colors.cardBg, padding: '24px', borderRadius: '20px',
              border: `1px solid ${colors.border}`,
              position: 'sticky', top: '100px', alignSelf: 'flex-start',
            }}
          >
            <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Beaker size={20} color={colors.primary} />
              {t('soil_sample_data')}
            </h3>

            {Object.entries(formData).map(([key, val]) => {
              if (key === 'drainage_issues' || key === 'compaction_issues') return null;
              return (
                <div key={key} style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: colors.textMuted, marginBottom: '4px' }}>
                    <span style={{ textTransform: 'capitalize' }}>{FIELD_LABELS[key] ?? key}</span>
                    <span style={{ color: colors.primary, fontWeight: '600' }}>{String(val)}</span>
                  </label>
                  <input
                    type="number" aria-label={FIELD_LABELS[key] ?? key} step="0.1" value={val}
                    onChange={(e) => setFormData({ ...formData, [key]: parseFloat(e.target.value) || 0 })}
                    style={{
                      width: '100%', padding: '10px 12px', borderRadius: '8px',
                      border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text,
                    }}
                  />
                </div>
              );
            })}

            {/* Issues checkboxes */}
            <div style={{ marginTop: '20px', marginBottom: '20px' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: '600', color: colors.danger, marginBottom: '12px' }}>
                {t('soil_physical_issues')}
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', cursor: 'pointer' }}>
                <input type="checkbox" checked={formData.drainage_issues}
                  onChange={(e) => setFormData({ ...formData, drainage_issues: e.target.checked })}
                  style={{ width: '18px', height: '18px' }} />
                <Droplet size={16} color={colors.accent} />
                <span style={{ fontSize: '0.9rem', color: colors.text }}>
                  {t('soil_drainage_issues')}
                </span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                <input type="checkbox" checked={formData.compaction_issues}
                  onChange={(e) => setFormData({ ...formData, compaction_issues: e.target.checked })}
                  style={{ width: '18px', height: '18px' }} />
                <Shield size={16} color={colors.accent} />
                <span style={{ fontSize: '0.9rem', color: colors.text }}>
                  {t('soil_compaction')}
                </span>
              </label>
            </div>

            {error && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px',
                padding: '10px', background: `${colors.danger}15`, borderRadius: '8px',
                fontSize: '0.85rem', color: colors.danger,
              }}>
                <AlertCircle size={16} /> {error}
              </div>
            )}

            <motion.button
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              onClick={analyze} disabled={loading}
              style={{
                width: '100%', padding: '14px',
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                color: 'white', border: 'none', borderRadius: '10px',
                fontWeight: '600', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              }}
            >
              <Send size={18} />
              {loading ? t('soil_analyzing') : t('soil_analyze')}
            </motion.button>
          </motion.div>

          {/* RIGHT: Results */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {!result ? (
              <div style={{
                background: colors.cardBg, padding: '80px 24px', borderRadius: '20px',
                border: `1px solid ${colors.border}`, textAlign: 'center', color: colors.textMuted,
              }}>
                <Leaf size={48} style={{ marginBottom: '16px', opacity: 0.3 }} />
                <p>{t('soil_empty_hint')}</p>
              </div>
            ) : (
              <>
                {/* Health + Triangle */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '20px' }}>
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                    style={{
                      background: colors.cardBg, padding: '24px', borderRadius: '20px',
                      border: `1px solid ${colors.border}`,
                    }}
                  >
                    <HealthGauge score={result.analysis.health_score} />
                    <div style={{ marginTop: '16px', padding: '10px', background: `${colors.primary}10`, borderRadius: '10px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                        {t('soil_fertility')}
                      </div>
                      <div style={{ fontSize: '1rem', fontWeight: '700', color: colors.primary, textTransform: 'capitalize' }}>
                        {t(`soil_level_${result.analysis.fertility ?? 'moderate'}`)}
                      </div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                    style={{
                      background: colors.cardBg, padding: '20px', borderRadius: '20px',
                      border: `1px solid ${colors.border}`,
                    }}
                  >
                    <h4 style={{ color: colors.text, marginBottom: '12px', fontSize: '1rem' }}>
                      {t('soil_texture_triangle')}
                    </h4>
                    <SoilTriangle clay={formData.clay} silt={formData.silt} sand={formData.sand} />
                    <div style={{ textAlign: 'center', marginTop: '12px', padding: '10px', background: `${colors.accent}10`, borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                        {t('soil_classification')}:{' '}
                      </span>
                      <span style={{ fontWeight: '700', color: colors.accent, textTransform: 'capitalize' }}>
                        {t(`soil_texture_${result.analysis.texture ?? 'loam'}`)}
                      </span>
                    </div>
                  </motion.div>
                </div>

                {/* Nutrients */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  style={{
                    background: colors.cardBg, padding: '24px', borderRadius: '20px',
                    border: `1px solid ${colors.border}`,
                  }}
                >
                  <h4 style={{ color: colors.text, marginBottom: '20px' }}>
                    {t('soil_nutrients')}
                  </h4>
                  <NutrientMeter name="pH" value={formData.pH} unit="" min={0} max={14} optimal={[6.0, 7.5]} />
                  <NutrientMeter name={t('soil_field_organic_matter')} value={formData.organic_matter} unit="%" min={0} max={10} optimal={[2, 5]} />
                  <NutrientMeter name={`${t('soil_field_nitrogen')} (N)`} value={formData.nitrogen} unit="ppm" min={0} max={150} optimal={[30, 80]} />
                  <NutrientMeter name={`${t('soil_field_phosphorus')} (P)`} value={formData.phosphorus} unit="ppm" min={0} max={100} optimal={[20, 60]} />
                  <NutrientMeter name={`${t('soil_field_potassium')} (K)`} value={formData.potassium} unit="ppm" min={0} max={500} optimal={[100, 300]} />
                </motion.div>

                {/* Problems */}
                {result.problems && result.problems.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    style={{
                      background: `linear-gradient(135deg, ${colors.danger}10, ${colors.warm}10)`,
                      padding: '24px', borderRadius: '20px',
                      border: `2px solid ${colors.danger}30`,
                    }}
                  >
                    <h4 style={{ color: colors.danger, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <AlertTriangle size={20} />
                      {t('soil_problems')} ({result.problems.length})
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                      {result.problems.map((p: any, i: number) => (
                        <div key={i} style={{
                          padding: '8px 14px', borderRadius: '100px',
                          background: p.severity === 'high' ? colors.danger : colors.warm,
                          color: 'white', fontSize: '0.85rem', fontWeight: '600',
                        }}>
                          {t(`soil_problem_${p.type}`)} ({t(`soil_severity_${p.severity}`)})
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* Remediation Solutions */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  style={{
                    background: colors.cardBg, borderRadius: '20px',
                    border: `1px solid ${colors.border}`, overflow: 'hidden',
                  }}
                >
                  {/* Tabs */}
                  <div style={{ display: 'flex', borderBottom: `2px solid ${colors.border}` }}>
                    {[
                      { key: 'organic' as const, label: t('soil_tab_organic'), color: colors.success },
                      { key: 'chemical' as const, label: t('soil_tab_chemical'), color: colors.warm },
                      { key: 'biological' as const, label: t('soil_tab_biological'), color: colors.accent },
                    ].map((tab) => (
                      <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        style={{
                          flex: 1, padding: '16px',
                          background: activeTab === tab.key ? `${tab.color}20` : 'transparent',
                          color: activeTab === tab.key ? tab.color : colors.textMuted,
                          border: 'none',
                          borderBottom: activeTab === tab.key ? `3px solid ${tab.color}` : '3px solid transparent',
                          cursor: 'pointer', fontSize: '0.9rem', fontWeight: '600',
                        }}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* Solutions */}
                  <div style={{ padding: '24px' }}>
                    {activeTab === 'organic' && result.organic_solutions?.length > 0 && (
                      <div>
                        <div style={{
                          padding: '12px 16px', background: `${colors.success}15`,
                          borderRadius: '10px', marginBottom: '16px',
                          fontSize: '0.85rem', color: colors.success,
                        }}>
                          <CheckCircle2 size={14} style={{ display: 'inline', marginRight: '6px' }} />
                          {t('soil_organic_banner')}
                        </div>
                        {result.organic_solutions.map((sol: any, i: number) => (
                          <SolutionCard key={i} solution={sol} colors={colors} t={t} expanded={expandedSolution === `org-${i}`} onToggle={() => setExpandedSolution(expandedSolution === `org-${i}` ? null : `org-${i}`)} />
                        ))}
                      </div>
                    )}

                    {activeTab === 'chemical' && result.chemical_solutions?.length > 0 && (
                      <div>
                        <div style={{
                          padding: '12px 16px', background: `${colors.warm}15`,
                          borderRadius: '10px', marginBottom: '16px',
                          border: `2px solid ${colors.warm}40`,
                          fontSize: '0.85rem', color: colors.warm,
                        }}>
                          <AlertTriangle size={14} style={{ display: 'inline', marginRight: '6px' }} />
                          <strong>{t('soil_chemical_warning')}:</strong> {t('soil_chemical_banner')}
                        </div>
                        {result.chemical_solutions.map((sol: any, i: number) => (
                          <SolutionCard key={i} solution={sol} colors={colors} t={t} expanded={expandedSolution === `chem-${i}`} onToggle={() => setExpandedSolution(expandedSolution === `chem-${i}` ? null : `chem-${i}`)} isWarning />
                        ))}
                      </div>
                    )}

                    {activeTab === 'biological' && result.biological_solutions?.length > 0 && (
                      <div>
                        <div style={{
                          padding: '12px 16px', background: `${colors.accent}15`,
                          borderRadius: '10px', marginBottom: '16px',
                          fontSize: '0.85rem', color: colors.accent,
                        }}>
                          <Bug size={14} style={{ display: 'inline', marginRight: '6px' }} />
                          {t('soil_biological_banner')}
                        </div>
                        {result.biological_solutions.map((sol: any, i: number) => (
                          <SolutionCard key={i} solution={sol} colors={colors} t={t} expanded={expandedSolution === `bio-${i}`} onToggle={() => setExpandedSolution(expandedSolution === `bio-${i}` ? null : `bio-${i}`)} />
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>

                {/* Drainage Plan */}
                {result.drainage_plan && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    style={{
                      background: colors.cardBg, padding: '24px', borderRadius: '20px',
                      border: `2px solid ${colors.accent}40`,
                    }}
                  >
                    <h4 style={{ color: colors.accent, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Droplet size={20} />
                      {t('soil_drainage_plan')}
                    </h4>
                    <h5 style={{ color: colors.text, fontSize: '0.9rem', marginBottom: '8px' }}>
                      {t('soil_immediate_actions')}:
                    </h5>
                    <ul style={{ paddingLeft: '20px', color: colors.text, fontSize: '0.85rem', lineHeight: '1.8', marginBottom: '16px' }}>
                      {(result.drainage_plan.immediate_actions ?? []).map((a: string, i: number) => (
                        <li key={i}>{a.startsWith('soil_action_') ? t(a) : a}</li>
                      ))}
                    </ul>
                    <h5 style={{ color: colors.text, fontSize: '0.9rem', marginBottom: '8px' }}>
                      {t('soil_long_term_solutions')}:
                    </h5>
                    <ul style={{ paddingLeft: '20px', color: colors.text, fontSize: '0.85rem', lineHeight: '1.8' }}>
                      {(result.drainage_plan.long_term_solutions ?? []).map((s: string, i: number) => (
                        <li key={i}>{s.startsWith('soil_action_') ? t(s) : s}</li>
                      ))}
                    </ul>
                    {result.drainage_plan.estimated_cost && (
                      <div style={{ marginTop: '12px', padding: '10px', background: `${colors.accent}10`, borderRadius: '8px', fontSize: '0.85rem', color: colors.text }}>
                        <strong>{t('soil_estimated_cost')}:</strong>{' '}
                        {typeof result.drainage_plan.estimated_cost === 'object'
                          ? (result.drainage_plan.estimated_cost[locale] ?? result.drainage_plan.estimated_cost.en)
                          : result.drainage_plan.estimated_cost}
                      </div>
                    )}
                  </motion.div>
                )}

                {/* History */}
                {history.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                    style={{
                      background: colors.cardBg, padding: '24px', borderRadius: '20px',
                      border: `1px solid ${colors.border}`,
                    }}
                  >
                    <h4 style={{ color: colors.text, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <History size={20} color={colors.accent} />
                      {t('soil_history')} ({history.length})
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto' }}>
                      {history.map((h, i) => (
                        <div key={h.id || i} style={{
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          padding: '12px', background: colors.bg, borderRadius: '10px',
                        }}>
                          <div>
                            <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                              {h.analyzed_at ? new Date(h.analyzed_at).toLocaleString() : ''}
                            </div>
                            <div style={{ fontSize: '0.9rem', color: colors.text }}>
                              {t(`soil_texture_${h.texture ?? 'loam'}`)} — {t(`soil_ph_${h.ph_status ?? 'neutral'}`)}
                            </div>
                          </div>
                          <div style={{ fontWeight: '700', color: colors.text }}>{h.health_score}</div>
                        </div>
                      ))}
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

function SolutionCard({ solution, colors, expanded, onToggle, t, isWarning = false }: any) {
  return (
    <motion.div
      layout
      style={{
        background: colors.bg, borderRadius: '12px',
        border: isWarning ? `2px solid ${colors.warm}40` : `1px solid ${colors.border}`,
        marginBottom: '12px', overflow: 'hidden',
      }}
    >
      <button onClick={onToggle} style={{
        width: '100%', padding: '16px', background: 'transparent', border: 'none',
        cursor: 'pointer', textAlign: 'start', display: 'flex', alignItems: 'center', gap: '12px',
      }}>
        <div style={{
          width: '32px', height: '32px', borderRadius: '50%',
          background: isWarning ? colors.warm : colors.success,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'white', fontSize: '0.85rem', fontWeight: '700',
        }}>
          {solution.priority}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '1rem', fontWeight: '600', color: colors.text }}>{solution.title}</div>
          <div style={{ fontSize: '0.8rem', color: colors.textMuted, marginTop: '2px' }}>
            {String(solution.time_to_effect).startsWith('soil_time_') ? t(String(solution.time_to_effect)) : solution.time_to_effect}{' — '}{String(solution.cost_estimate).startsWith('soil_cost_') ? t(String(solution.cost_estimate)) : solution.cost_estimate}
          </div>
        </div>
        {expanded ? <ChevronUp size={20} color={colors.textMuted} /> : <ChevronDown size={20} color={colors.textMuted} />}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '0 16px 16px 16px' }}>
              <p style={{ color: colors.text, fontSize: '0.9rem', lineHeight: '1.6', marginBottom: '16px' }}>
                {solution.description}
              </p>

              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: '600', color: colors.success, marginBottom: '6px' }}>
                  ✓ {t('soil_benefits')}:
                </div>
                <ul style={{ paddingLeft: '20px', color: colors.text, fontSize: '0.85rem', lineHeight: '1.8' }}>
                  {(solution.benefits ?? []).map((b: string, i: number) => (
                    <li key={i}>{b.startsWith('soil_benefit_') ? t(b) : b}</li>
                  ))}
                </ul>
              </div>

              {solution.risks && solution.risks.length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: '600', color: colors.danger, marginBottom: '6px' }}>
                    ⚠ {t('soil_risks')}:
                  </div>
                  <ul style={{ paddingLeft: '20px', color: colors.text, fontSize: '0.85rem', lineHeight: '1.8' }}>
                    {(solution.risks ?? []).map((r: string, i: number) => (
                    <li key={i}>{r.startsWith('soil_risk_') ? t(r) : r}</li>
                  ))}
                  </ul>
                </div>
              )}

              <div style={{ padding: '12px', background: `${colors.primary}10`, borderRadius: '8px', fontSize: '0.85rem', color: colors.text }}>
                <strong>{t('soil_application')}:</strong>{' '}
{String(solution.application_rate).startsWith('soil_apply_')
  ? t(String(solution.application_rate))
  : solution.application_rate}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <SoilDashboard />
    </motion.div>
  );
}
