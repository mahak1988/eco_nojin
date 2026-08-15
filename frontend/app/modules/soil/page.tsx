"use client";
import { useState, useEffect } from 'react';
import Navbar from '../../../components/layout/Navbar';
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
  ChevronDown, ChevronUp
} from 'lucide-react';

export default function SoilPage() {
  const { t, direction, language } = useI18n();
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
      language: language === 'fa' ? 'fa' : 'en',
    });
    
    if (res.success) {
      setResult(res.data);
      if (selectedFarm) loadHistory();
    } else {
      setError(res.error || 'Analysis failed');
    }
    setLoading(false);
  };

  const currentLang = language === 'fa' ? 'fa' : 'en';

  return (
    <div dir={direction} style={{ background: colors.bg, minHeight: '100vh' }}>
      <Navbar />
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
                {currentLang === 'fa' ? 'تحلیل و اصلاح خاک' : 'Soil Analysis & Remediation'}
              </h1>
              <p style={{ margin: '4px 0 0', opacity: 0.95 }}>
                {currentLang === 'fa' 
                  ? 'تحلیل کامل با توصیه‌های ارگانیک، شیمیایی و بیولوژیک'
                  : 'Comprehensive analysis with organic, chemical, and biological remediation'}
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
              {currentLang === 'fa' ? 'داده‌های نمونه خاک' : 'Soil Sample Data'}
            </h3>

            {Object.entries(formData).map(([key, val]) => {
              if (key === 'drainage_issues' || key === 'compaction_issues') return null;
              return (
                <div key={key} style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: colors.textMuted, marginBottom: '4px' }}>
                    <span style={{ textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</span>
                    <span style={{ color: colors.primary, fontWeight: '600' }}>{String(val)}</span>
                  </label>
                  <input
                    type="number" step="0.1" value={val}
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
                {currentLang === 'fa' ? 'مشکلات فیزیکی' : 'Physical Issues'}
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', cursor: 'pointer' }}>
                <input type="checkbox" checked={formData.drainage_issues}
                  onChange={(e) => setFormData({ ...formData, drainage_issues: e.target.checked })}
                  style={{ width: '18px', height: '18px' }} />
                <Droplet size={16} color={colors.accent} />
                <span style={{ fontSize: '0.9rem', color: colors.text }}>
                  {currentLang === 'fa' ? 'مشکل زهکشی' : 'Drainage Issues'}
                </span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                <input type="checkbox" checked={formData.compaction_issues}
                  onChange={(e) => setFormData({ ...formData, compaction_issues: e.target.checked })}
                  style={{ width: '18px', height: '18px' }} />
                <Shield size={16} color={colors.accent} />
                <span style={{ fontSize: '0.9rem', color: colors.text }}>
                  {currentLang === 'fa' ? 'تراکم خاک' : 'Soil Compaction'}
                </span>
              </label>
            </div>

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
              {loading ? '...' : (currentLang === 'fa' ? 'تحلیل خاک' : 'Analyze Soil')}
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
                <p>{currentLang === 'fa' ? 'داده‌های خاک را وارد کنید' : 'Fill in soil data to see results'}</p>
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
                        {currentLang === 'fa' ? 'حاصلخیزی' : 'Fertility'}
                      </div>
                      <div style={{ fontSize: '1rem', fontWeight: '700', color: colors.primary, textTransform: 'capitalize' }}>
                        {result.analysis.fertility}
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
                      {currentLang === 'fa' ? 'مثلث بافت USDA' : 'USDA Texture Triangle'}
                    </h4>
                    <SoilTriangle clay={formData.clay} silt={formData.silt} sand={formData.sand} />
                    <div style={{ textAlign: 'center', marginTop: '12px', padding: '10px', background: `${colors.accent}10`, borderRadius: '10px' }}>
                      <span style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                        {currentLang === 'fa' ? 'طبقه‌بندی: ' : 'Classification: '}
                      </span>
                      <span style={{ fontWeight: '700', color: colors.accent, textTransform: 'capitalize' }}>
                        {result.analysis.texture}
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
                    {currentLang === 'fa' ? 'تحلیل مواد مغذی' : 'Nutrient Analysis'}
                  </h4>
                  <NutrientMeter name="pH" value={formData.pH} unit="" min={0} max={14} optimal={[6.0, 7.5]} />
                  <NutrientMeter name={currentLang === 'fa' ? 'ماده آلی' : 'Organic Matter'} value={formData.organic_matter} unit="%" min={0} max={10} optimal={[2, 5]} />
                  <NutrientMeter name={currentLang === 'fa' ? 'نیتروژن (N)' : 'Nitrogen (N)'} value={formData.nitrogen} unit="ppm" min={0} max={150} optimal={[30, 80]} />
                  <NutrientMeter name={currentLang === 'fa' ? 'فسفر (P)' : 'Phosphorus (P)'} value={formData.phosphorus} unit="ppm" min={0} max={100} optimal={[20, 60]} />
                  <NutrientMeter name={currentLang === 'fa' ? 'پتاسیم (K)' : 'Potassium (K)'} value={formData.potassium} unit="ppm" min={0} max={500} optimal={[100, 300]} />
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
                      {currentLang === 'fa' ? 'مشکلات شناسایی شده' : 'Problems Identified'} ({result.problems.length})
                    </h4>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                      {result.problems.map((p: any, i: number) => (
                        <div key={i} style={{
                          padding: '8px 14px', borderRadius: '100px',
                          background: p.severity === 'high' ? colors.danger : colors.warm,
                          color: 'white', fontSize: '0.85rem', fontWeight: '600',
                        }}>
                          {p.type.replace(/_/g, ' ')} ({p.severity})
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
                      { key: 'organic' as const, label: currentLang === 'fa' ? '🌱 ارگانیک' : '🌱 Organic', color: colors.success },
                      { key: 'chemical' as const, label: currentLang === 'fa' ? '⚗️ شیمیایی' : '⚗️ Chemical', color: colors.warm },
                      { key: 'biological' as const, label: currentLang === 'fa' ? '🦠 بیولوژیک' : '🦠 Biological', color: colors.accent },
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
                          {currentLang === 'fa' 
                            ? 'اولویت ۱ - توصیه شده - پایدار و ایمن'
                            : 'Priority 1 - Recommended - Sustainable and safe'}
                        </div>
                        {result.organic_solutions.map((sol: any, i: number) => (
                          <SolutionCard key={i} solution={sol} colors={colors} currentLang={currentLang} expanded={expandedSolution === `org-${i}`} onToggle={() => setExpandedSolution(expandedSolution === `org-${i}` ? null : `org-${i}`)} />
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
                          <strong>{currentLang === 'fa' ? 'هشدار:' : 'WARNING:'}</strong> {currentLang === 'fa' ? 'اولویت ۲ - عوارض جانبی جدی' : 'Priority 2 - Serious side effects'}
                        </div>
                        {result.chemical_solutions.map((sol: any, i: number) => (
                          <SolutionCard key={i} solution={sol} colors={colors} currentLang={currentLang} expanded={expandedSolution === `chem-${i}`} onToggle={() => setExpandedSolution(expandedSolution === `chem-${i}` ? null : `chem-${i}`)} isWarning />
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
                          {currentLang === 'fa' ? 'احیای حیات خاک - طولانی‌مدت' : 'Restore soil life - Long-term'}
                        </div>
                        {result.biological_solutions.map((sol: any, i: number) => (
                          <SolutionCard key={i} solution={sol} colors={colors} currentLang={currentLang} expanded={expandedSolution === `bio-${i}`} onToggle={() => setExpandedSolution(expandedSolution === `bio-${i}` ? null : `bio-${i}`)} />
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
                      {currentLang === 'fa' ? 'برنامه زهکشی' : 'Drainage Plan'}
                    </h4>
                    <h5 style={{ color: colors.text, fontSize: '0.9rem', marginBottom: '8px' }}>
                      {currentLang === 'fa' ? 'اقدامات فوری:' : 'Immediate Actions:'}
                    </h5>
                    <ul style={{ paddingLeft: '20px', color: colors.text, fontSize: '0.85rem', lineHeight: '1.8', marginBottom: '16px' }}>
                      {result.drainage_plan.immediate_actions.map((a: string, i: number) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                    <h5 style={{ color: colors.text, fontSize: '0.9rem', marginBottom: '8px' }}>
                      {currentLang === 'fa' ? 'راه‌حل‌های بلندمدت:' : 'Long-term Solutions:'}
                    </h5>
                    <ul style={{ paddingLeft: '20px', color: colors.text, fontSize: '0.85rem', lineHeight: '1.8' }}>
                      {result.drainage_plan.long_term_solutions.map((s: string, i: number) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
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
                      {currentLang === 'fa' ? 'تاریخچه' : 'History'} ({history.length})
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
                              {h.texture} • {h.ph_status}
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

function SolutionCard({ solution, colors, expanded, onToggle, currentLang, isWarning = false }: any) {
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
            {solution.time_to_effect} • {solution.cost_estimate}
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
                  ✓ {currentLang === 'fa' ? 'مزایا:' : 'Benefits:'}
                </div>
                <ul style={{ paddingLeft: '20px', color: colors.text, fontSize: '0.85rem', lineHeight: '1.8' }}>
                  {solution.benefits.map((b: string, i: number) => <li key={i}>{b}</li>)}
                </ul>
              </div>

              {solution.risks && solution.risks.length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: '600', color: colors.danger, marginBottom: '6px' }}>
                    ⚠️ {currentLang === 'fa' ? 'خطرات:' : 'Risks:'}
                  </div>
                  <ul style={{ paddingLeft: '20px', color: colors.text, fontSize: '0.85rem', lineHeight: '1.8' }}>
                    {solution.risks.map((r: string, i: number) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}

              <div style={{ padding: '12px', background: `${colors.primary}10`, borderRadius: '8px', fontSize: '0.85rem', color: colors.text }}>
                <strong>{currentLang === 'fa' ? 'نرخ کاربرد:' : 'Application:'}</strong> {solution.application_rate}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
