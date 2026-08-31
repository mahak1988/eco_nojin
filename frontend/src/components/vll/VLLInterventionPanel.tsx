import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, Trees, Layers, Droplets, Sprout, Wind } from 'lucide-react';
import { Card, Button } from '../ui';

interface Intervention {
  id: string;
  name: string;
  category: string;
  icon: React.ReactNode;
  color: string;
  description: string;
  parameters?: any;
  position?: { x: number; z: number };
  coverage?: number;
}

const AVAILABLE_INTERVENTIONS: Intervention[] = [
  {
    id: 'tree_planting',
    name: 'کاشت بادشکن',
    category: 'biological',
    icon: <Trees size={20} />,
    color: '#15803d',
    description: 'ردیف درختان برای کاهش سرعت باد',
  },
  {
    id: 'terrace',
    name: 'تراس‌بندی',
    category: 'engineering',
    icon: <Layers size={20} />,
    color: '#78716c',
    description: 'پله‌های عرضی برای کنترل رواناب',
  },
  {
    id: 'check_dam',
    name: 'بندسار',
    category: 'engineering',
    icon: <Layers size={20} />,
    color: '#64748b',
    description: 'سد کوچک رسوبگیر در آبراهه',
  },
  {
    id: 'crop_planting',
    name: 'کشت محصول',
    category: 'agronomic',
    icon: <Sprout size={20} />,
    color: '#84cc16',
    description: 'کاشت گندم، جو یا ذرت',
  },
  {
    id: 'cover_crop',
    name: 'گیاه پوششی',
    category: 'biological',
    icon: <Sprout size={20} />,
    color: '#22c55e',
    description: 'شبدر یا یونجه برای حفاظت خاک',
  },
  {
    id: 'crescent_bunds',
    name: 'هلالی آبگیر',
    category: 'engineering',
    icon: <Droplets size={20} />,
    color: '#3b82f6',
    description: 'جمع‌آوری آب باران',
  },
];

interface InterventionPanelProps {
  interventions: any[];
  onAdd: (intv: any) => void;
  onRemove: (id: number) => void;
}

export const InterventionPanel: React.FC<InterventionPanelProps> = ({
  interventions,
  onAdd,
  onRemove,
}) => {
  const [configuring, setConfiguring] = useState<Intervention | null>(null);
  const [params, setParams] = useState<any>({});
  const [coverage, setCoverage] = useState(100);
  const [position, setPosition] = useState({ x: 0, z: 0 });

  const startConfig = (intv: Intervention) => {
    setConfiguring(intv);
    setParams({});
    setCoverage(100);
    setPosition({ x: 0, z: 0 });
  };

  const confirmAdd = () => {
    if (!configuring) return;
    onAdd({
      ...configuring,
      parameters: params,
      coverage,
      position,
    });
    setConfiguring(null);
  };

  return (
    <Card title="🛠️ کتابخانه مداخلات" icon={<Wind size={18} />}>
      <p style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', marginBottom: '1rem' }}>
        برای هر مداخله، پارامترها را تنظیم و روی زمین قرار دهید
      </p>

      {/* Active Interventions */}
      {interventions.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <h4 style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>
            ✅ فعال ({interventions.length})
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {interventions.map((intv) => (
              <motion.div
                key={intv.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  background: `${intv.color}15`,
                  border: `1px solid ${intv.color}40`,
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.75rem',
                }}
              >
                <span style={{ color: intv.color }}>{intv.icon}</span>
                <span style={{ flex: 1 }}>{intv.name}</span>
                <button
                  onClick={() => onRemove(intv.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--color-error)',
                  }}
                >
                  <Trash2 size={14} />
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Available Interventions */}
      <h4 style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>📦 مداخلات موجود</h4>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
        {AVAILABLE_INTERVENTIONS.map((intv) => (
          <motion.button
            key={intv.id}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => startConfig(intv)}
            style={{
              padding: '0.75rem',
              background: `${intv.color}10`,
              border: `1px solid ${intv.color}40`,
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '0.25rem',
              color: intv.color,
              fontSize: '0.75rem',
            }}
          >
            {intv.icon}
            <span>{intv.name}</span>
          </motion.button>
        ))}
      </div>

      {/* Configuration Modal */}
      <AnimatePresence>
        {configuring && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setConfiguring(null)}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.7)',
              backdropFilter: 'blur(4px)',
              zIndex: 1000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              style={{
                background: 'var(--color-surface)',
                borderRadius: 'var(--radius-2xl)',
                padding: '2rem',
                maxWidth: 500,
                width: '90%',
                boxShadow: 'var(--shadow-2xl)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  marginBottom: '1.5rem',
                }}
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: 'var(--radius-xl)',
                    background: `${configuring.color}20`,
                    color: configuring.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {configuring.icon}
                </div>
                <div>
                  <h3 style={{ margin: 0 }}>{configuring.name}</h3>
                  <p
                    style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}
                  >
                    {configuring.description}
                  </p>
                </div>
              </div>

              {/* Coverage Slider */}
              <div style={{ marginBottom: '1rem' }}>
                <label
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.875rem',
                    marginBottom: '0.25rem',
                  }}
                >
                  <span>پوشش زمین</span>
                  <strong>{coverage}٪</strong>
                </label>
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="5"
                  value={coverage}
                  onChange={(e) => setCoverage(parseInt(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>

              {/* Position */}
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                  📍 موقعیت روی زمین
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                      X
                    </div>
                    <input
                      type="number"
                      value={position.x}
                      onChange={(e) => setPosition({ ...position, x: parseFloat(e.target.value) })}
                      className="input"
                      style={{ padding: '0.5rem' }}
                    />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                      Z
                    </div>
                    <input
                      type="number"
                      value={position.z}
                      onChange={(e) => setPosition({ ...position, z: parseFloat(e.target.value) })}
                      className="input"
                      style={{ padding: '0.5rem' }}
                    />
                  </div>
                </div>
              </div>

              {/* Intervention-specific parameters */}
              {configuring.id === 'tree_planting' && (
                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                    🌳 گونه درخت
                  </label>
                  <select
                    value={params.species || 'cypress'}
                    onChange={(e) => setParams({ ...params, species: e.target.value })}
                    className="input"
                  >
                    <option value="cypress">سرو (بادشکن قوی)</option>
                    <option value="pine">کاج</option>
                    <option value="olive">زیتون (مثمر)</option>
                    <option value="almond">بادام (مثمر)</option>
                    <option value="oak">بلوط (بومی)</option>
                  </select>
                  <label
                    style={{
                      fontSize: '0.875rem',
                      display: 'block',
                      marginTop: '0.5rem',
                      marginBottom: '0.25rem',
                    }}
                  >
                    تعداد درختان: {params.count || 10}
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="50"
                    value={params.count || 10}
                    onChange={(e) => setParams({ ...params, count: parseInt(e.target.value) })}
                    style={{ width: '100%' }}
                  />
                  <label
                    style={{
                      fontSize: '0.875rem',
                      display: 'block',
                      marginTop: '0.5rem',
                      marginBottom: '0.25rem',
                    }}
                  >
                    تعداد ردیف: {params.rows || 3}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={params.rows || 3}
                    onChange={(e) => setParams({ ...params, rows: parseInt(e.target.value) })}
                    style={{ width: '100%' }}
                  />
                </div>
              )}

              {configuring.id === 'terrace' && (
                <div style={{ marginBottom: '1rem' }}>
                  <label
                    style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem' }}
                  >
                    تعداد تراس: {params.count || 5}
                  </label>
                  <input
                    type="range"
                    min="2"
                    max="20"
                    value={params.count || 5}
                    onChange={(e) => setParams({ ...params, count: parseInt(e.target.value) })}
                    style={{ width: '100%' }}
                  />
                  <label
                    style={{
                      fontSize: '0.875rem',
                      display: 'block',
                      marginTop: '0.5rem',
                      marginBottom: '0.25rem',
                    }}
                  >
                    فاصله (متر): {params.spacing || 8}
                  </label>
                  <input
                    type="range"
                    min="3"
                    max="20"
                    value={params.spacing || 8}
                    onChange={(e) => setParams({ ...params, spacing: parseInt(e.target.value) })}
                    style={{ width: '100%' }}
                  />
                </div>
              )}

              {configuring.id === 'check_dam' && (
                <div style={{ marginBottom: '1rem' }}>
                  <label
                    style={{ fontSize: '0.875rem', display: 'block', marginBottom: '0.25rem' }}
                  >
                    تعداد بندسار: {params.count || 6}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={params.count || 6}
                    onChange={(e) => setParams({ ...params, count: parseInt(e.target.value) })}
                    style={{ width: '100%' }}
                  />
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button
                  variant="secondary"
                  onClick={() => setConfiguring(null)}
                  style={{ flex: 1 }}
                >
                  انصراف
                </Button>
                <Button variant="primary" onClick={confirmAdd} style={{ flex: 1 }}>
                  <Plus size={16} /> افزودن به زمین
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
};
