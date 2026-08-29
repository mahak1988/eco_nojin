/**
 * Models Library - Browse and run all scientific models
 * Displays 21 scientific motors from the backend
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Database, Search, Filter, Play, Info,
  Zap, Leaf, Droplet, Mountain, Wind, Flame,
  ChartBar, TrendingUp, Grid, Layers, X
} from 'lucide-react';
import motorsService, { Motor } from '../services/motorsService';
import MotorSimulator from '../components/simulators/MotorSimulator';
import "./admin/AdminTheme.css";

const CATEGORY_ICONS: Record<string, any> = {
  'Crop': Leaf,
  'Soil': Layers,
  'Hydrology': Droplet,
  'Hydraulics': Wind,
  'Carbon': Flame,
  'Irrigation': Droplet,
  'Land': Mountain,
  'Other': Grid,
};

const CATEGORY_COLORS: Record<string, string> = {
  'Crop': '#10b981',
  'Soil': '#8b5cf6',
  'Hydrology': '#3b82f6',
  'Hydraulics': '#06b6d4',
  'Carbon': '#f59e0b',
  'Irrigation': '#14b8a6',
  'Land': '#f97316',
  'Other': '#6b7280',
};

export default function ModelsLibrary() {
  const { t } = useTranslation();
  const [motors, setMotors] = useState<Motor[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedMotor, setSelectedMotor] = useState<Motor | null>(null);

  useEffect(() => {
    fetchMotors();
  }, []);

  const fetchMotors = async () => {
    try {
      const data = await motorsService.listMotors();
      setMotors(data);
    } catch (error) {
      console.error('Failed to fetch motors:', error);
    } finally {
      setLoading(false);
    }
  };

  const categories = ['all', ...Array.from(new Set(motors.map(m => m.category || 'Other')))];

  const filteredMotors = motors.filter(motor => {
    const matchesCategory = selectedCategory === 'all' || motor.category === selectedCategory;
    const matchesSearch = searchQuery === '' ||
      motor.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      motor.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  if (loading) {
    return (
      <div className="admin-page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">
              <Database size={32} /> {t('nav.models', 'Models Library')}
            </h1>
            <p className="page-subtitle">{t('simulator.loading', 'Loading models...')}</p>
          </div>
        </div>
        <div className="grid-3col">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="glass-card" style={{ padding: '24px' }}>
              <div className="skeleton" style={{ height: '20px', width: '60%', marginBottom: '12px' }}></div>
              <div className="skeleton" style={{ height: '14px', marginBottom: '8px' }}></div>
              <div className="skeleton" style={{ height: '14px', marginBottom: '8px' }}></div>
              <div className="skeleton" style={{ height: '40px', marginTop: '16px' }}></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page-container">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Database size={32} style={{ color: 'var(--accent-primary)' }} />
            {t('nav.models', 'Models Library')}
          </h1>
          <p className="page-subtitle">
            {t('simulator.description', 'Browse and run 21 scientific models')}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span className="status-badge info">
            <Database size={14} /> {motors.length} models
          </span>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="filter-bar">
        <div style={{ position: 'relative', flex: 1, maxWidth: '300px' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            className="form-input"
            placeholder={t('admin.search', 'Search...')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: '36px' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {categories.map(cat => (
            <button
              key={cat}
              className={'filter-chip' + (selectedCategory === cat ? ' active' : '')}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat === 'all' ? t('common.all', 'All') : cat}
              <span style={{ marginLeft: '6px', fontSize: '11px', opacity: 0.7 }}>
                ({cat === 'all' ? motors.length : motors.filter(m => m.category === cat).length})
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Models Grid */}
      {filteredMotors.length === 0 ? (
        <div className="empty-state">
          <Database size={64} style={{ opacity: 0.3 }} />
          <div className="empty-state-icon">🔍</div>
          <div className="title">{t('common.noData', 'No models found')}</div>
          <div>{t('simulator.tryDifferentSearch', 'Try a different search')}</div>
        </div>
      ) : (
        <div className="grid-3col">
          {filteredMotors.map(motor => {
            const Icon = CATEGORY_ICONS[motor.category || 'Other'] || Grid;
            const color = CATEGORY_COLORS[motor.category || 'Other'] || '#6b7280';

            return (
              <div key={motor.key} className="glass-card" style={{ cursor: 'pointer' }} onClick={() => setSelectedMotor(motor)}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '16px' }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '12px',
                    background: `${color}20`,
                    color: color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    <Icon size={24} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 4px 0' }}>
                      {motor.name}
                    </h3>
                    <div style={{ fontSize: '11px', color: color, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px' }}>
                      {motor.category || 'Other'}
                    </div>
                  </div>
                </div>

                <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5', margin: '0 0 16px 0' }}>
                  {motor.description || 'No description available'}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-faint)' }}>
                    {motor.parameters?.length || 0} parameters
                  </span>
                  <button
                    className="btn-primary"
                    style={{ padding: '6px 16px', fontSize: '12px' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedMotor(motor);
                    }}
                  >
                    <Play size={14} /> {t('simulator.run', 'Run')}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Motor Simulator Modal */}
      {selectedMotor && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px',
          backdropFilter: 'blur(4px)',
        }} onClick={() => setSelectedMotor(null)}>
          <div style={{
            maxWidth: '1200px',
            width: '100%',
            maxHeight: '90vh',
            overflow: 'auto',
          }} onClick={(e) => e.stopPropagation()}>
            <MotorSimulator
              motor={selectedMotor}
              onClose={() => setSelectedMotor(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
