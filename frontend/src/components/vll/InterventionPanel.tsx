import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, Settings, Check } from 'lucide-react';
import { Card, Button } from '../ui';
import { INTERVENTIONS_LIBRARY } from '../../lib/interventions';
import type { Intervention, AppliedIntervention, InterventionCategory } from '../../types/vll';

interface InterventionPanelProps {
  appliedInterventions: AppliedIntervention[];
  onAdd: (intervention: AppliedIntervention) => void;
  onRemove: (index: number) => void;
  onUpdate: (index: number, intervention: AppliedIntervention) => void;
}

const CATEGORY_NAMES: Record<InterventionCategory, string> = {
  biological: '🌿 بیولوژیک',
  engineering: '🏗️ مهندسی آبخیزداری',
  agronomic: '🌾 زراعی',
  water_management: '💧 مدیریت آب',
  livestock: '🐄 دام و زنبورداری',
  integrated: '🌐 تلفیقی',
};

export const InterventionPanel: React.FC<InterventionPanelProps> = ({
  appliedInterventions,
  onAdd,
  onRemove,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<InterventionCategory>('biological');
  const [configuringId, setConfiguringId] = useState<string | null>(null);
  const [tempParams, setTempParams] = useState<Record<string, any>>({});
  const [tempCoverage, setTempCoverage] = useState(100);

  const categoryInterventions = INTERVENTIONS_LIBRARY.filter(i => i.category === selectedCategory);

  const startConfigure = (intervention: Intervention) => {
    setConfiguringId(intervention.id);
    const defaults: Record<string, any> = {};
    intervention.parameters.forEach(p => {
      defaults[p.key] = p.defaultValue;
    });
    setTempParams(defaults);
    setTempCoverage(100);
  };

  const confirmAdd = () => {
    if (!configuringId) return;
    onAdd({
      interventionId: configuringId,
      parameters: tempParams,
      appliedAt: new Date().toISOString(),
      coveragePct: tempCoverage,
    });
    setConfiguringId(null);
    setTempParams({});
  };

  const totalCost = appliedInterventions.reduce((sum, applied) => {
    const intervention = INTERVENTIONS_LIBRARY.find(i => i.id === applied.interventionId);
    return sum + (intervention?.estimatedCostUsd || 0) * (applied.coveragePct / 100);
  }, 0);

  return (
    <Card title="کتابخانه مداخلات" icon={<Settings size={20} />} subtitle={`${appliedInterventions.length} مداخله فعال - هزینه کل: $${totalCost.toLocaleString()}`}>
      {/* Applied Interventions List */}
      {appliedInterventions.length > 0 && (
        <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'var(--color-surface)', borderRadius: 'var(--radius-lg)' }}>
          <h4 style={{ marginBottom: '0.75rem', fontSize: '0.875rem' }}>✅ مداخلات انتخاب‌شده:</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {appliedInterventions.map((applied, index) => {
              const intervention = INTERVENTIONS_LIBRARY.find(i => i.id === applied.interventionId);
              if (!intervention) return null;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.5rem',
                    background: 'white',
                    borderRadius: 'var(--radius-md)',
                    border: `2px solid ${intervention.color}40`,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1.25rem' }}>{intervention.icon}</span>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{intervention.nameFa}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                        پوشش {applied.coveragePct}٪ - ${Math.round(intervention.estimatedCostUsd * applied.coveragePct / 100)}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => onRemove(index)}
                    className="btn btn-ghost"
                    style={{ padding: '0.25rem', color: 'var(--color-error)' }}
                  >
                    <Trash2 size={16} />
                  </button>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Category Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
        {(Object.keys(CATEGORY_NAMES) as InterventionCategory[]).map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`btn ${selectedCategory === cat ? 'btn-primary' : 'btn-secondary'}`}
            style={{ whiteSpace: 'nowrap', fontSize: '0.75rem', padding: '0.5rem 1rem' }}
          >
            {CATEGORY_NAMES[cat]}
          </button>
        ))}
      </div>

      {/* Interventions Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem' }}>
        {categoryInterventions.map((intervention) => {
          const isApplied = appliedInterventions.some(a => a.interventionId === intervention.id);
          return (
            <motion.div
              key={intervention.id}
              whileHover={{ y: -4 }}
              onClick={() => !isApplied && startConfigure(intervention)}
              style={{
                padding: '1rem',
                background: isApplied ? `${intervention.color}20` : 'var(--color-surface)',
                border: `2px solid ${isApplied ? intervention.color : 'var(--color-border)'}`,
                borderRadius: 'var(--radius-lg)',
                cursor: isApplied ? 'default' : 'pointer',
                opacity: isApplied ? 0.6 : 1,
                position: 'relative',
              }}
            >
              {isApplied && (
                <div style={{
                  position: 'absolute', top: 8, left: 8,
                  width: 20, height: 20, borderRadius: '50%',
                  background: 'var(--color-success)', color: 'white',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Check size={12} />
                </div>
              )}
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{intervention.icon}</div>
              <div style={{ fontWeight: 600, fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                {intervention.nameFa}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', marginBottom: '0.5rem', lineHeight: 1.4 }}>
                {intervention.description.slice(0, 50)}...
              </div>
              <div style={{ fontSize: '0.75rem', color: intervention.color, fontWeight: 600 }}>
                ${intervention.estimatedCostUsd} / هکتار
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Configuration Modal */}
      <AnimatePresence>
        {configuringId && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setConfiguringId(null)}
              style={{
                position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
                backdropFilter: 'blur(4px)', zIndex: 1000,
              }}
            />
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              style={{
                position: 'fixed', top: '50%', left: '50%',
                transform: 'translate(-50%, -50%)',
                background: 'var(--color-surface)', borderRadius: 'var(--radius-2xl)',
                padding: '2rem', maxWidth: 500, width: '90%', zIndex: 1001,
                boxShadow: 'var(--shadow-2xl)',
              }}
            >
              {(() => {
                const intervention = INTERVENTIONS_LIBRARY.find(i => i.id === configuringId);
                if (!intervention) return null;
                return (
                  <>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
                      <div style={{
                        width: 48, height: 48, borderRadius: 'var(--radius-xl)',
                        background: `${intervention.color}20`, color: intervention.color,
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem',
                      }}>
                        {intervention.icon}
                      </div>
                      <div>
                        <h3 style={{ margin: 0 }}>{intervention.nameFa}</h3>
                        <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                          مدل علمی: {intervention.scientificModel}
                        </p>
                      </div>
                    </div>

                    <div style={{ marginBottom: '1rem' }}>
                      <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                        {intervention.description}
                      </p>
                    </div>

                    {intervention.parameters.map((param) => (
                      <div key={param.key} style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 600 }}>
                          {param.labelFa} {param.unit && `(${param.unit})`}
                        </label>
                        {param.type === 'number' ? (
                          <>
                            <input
                              type="range"
                              min={param.min}
                              max={param.max}
                              step={param.step}
                              value={tempParams[param.key] || param.defaultValue}
                              onChange={(e) => setTempParams({ ...tempParams, [param.key]: parseFloat(e.target.value) })}
                              style={{ width: '100%' }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                              <span>{param.min}</span>
                              <strong>{tempParams[param.key] || param.defaultValue}</strong>
                              <span>{param.max}</span>
                            </div>
                          </>
                        ) : param.type === 'select' ? (
                          <select
                            value={tempParams[param.key] || param.defaultValue}
                            onChange={(e) => setTempParams({ ...tempParams, [param.key]: e.target.value })}
                            className="input"
                          >
                            {param.options?.map(opt => (
                              <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                          </select>
                        ) : null}
                      </div>
                    ))}

                    <div style={{ marginBottom: '1.5rem' }}>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 600 }}>
                        پوشش کل زمین (٪)
                      </label>
                      <input
                        type="range"
                        min="10"
                        max="100"
                        step="5"
                        value={tempCoverage}
                        onChange={(e) => setTempCoverage(parseInt(e.target.value))}
                        style={{ width: '100%' }}
                      />
                      <div style={{ textAlign: 'center', fontWeight: 600, color: intervention.color }}>
                        {tempCoverage}٪
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <Button variant="secondary" onClick={() => setConfiguringId(null)} style={{ flex: 1 }}>
                        انصراف
                      </Button>
                      <Button variant="primary" onClick={confirmAdd} style={{ flex: 1 }}>
                        <Plus size={16} /> افزودن به سناریو
                      </Button>
                    </div>
                  </>
                );
              })()}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </Card>
  );
};
