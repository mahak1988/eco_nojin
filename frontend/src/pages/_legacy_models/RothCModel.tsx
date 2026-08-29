/**
 * RothC Model Page - Soil Carbon Dynamics Simulation
 * Uses the RothCMotor from scientific_motors
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Layers, Play, Info, TrendingUp, AlertCircle,
  RefreshCw, Loader2, CheckCircle
} from 'lucide-react';
import motorsService from '../services/motorsService';
import MotorSimulator from '../components/simulators/MotorSimulator';
import "./admin/AdminTheme.css";

const ROTHC_MOTOR = {
  key: 'rothc',
  name: 'RothC',
  description: 'Soil carbon dynamics model - simulates carbon turnover in soil over time',
  category: 'Soil',
  parameters: [
    { name: 'initial_carbon', type: 'number', default: 20, min: 1, max: 100, description: 'Initial soil carbon (t/ha)' },
    { name: 'years', type: 'number', default: 10, min: 1, max: 100, description: 'Simulation years' },
    { name: 'clay_content', type: 'number', default: 25, min: 5, max: 70, description: 'Clay content (%)' },
    { name: 'monthly_rainfall', type: 'number', default: 50, min: 10, max: 500, description: 'Average monthly rainfall (mm)' },
    { name: 'monthly_temperature', type: 'number', default: 15, min: -20, max: 50, description: 'Average monthly temperature (°C)' },
    { name: 'carbon_input', type: 'number', default: 1.5, min: 0.1, max: 10, description: 'Annual carbon input (t/ha/year)' },
  ],
};

export default function RothCModel() {
  const { t } = useTranslation();
  const [showInfo, setShowInfo] = useState(false);

  return (
    <div className="admin-page-container">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Layers size={32} style={{ color: '#8b5cf6' }} />
            {t('nav.rothc', 'RothC Model')}
          </h1>
          <p className="page-subtitle">
            {t('simulator.rothcDescription', 'Soil carbon dynamics simulation')}
          </p>
        </div>
        <button className="btn-secondary" onClick={() => setShowInfo(!showInfo)}>
          <Info size={16} /> {t('simulator.aboutModel', 'About Model')}
        </button>
      </div>

      {/* Info Card */}
      {showInfo && (
        <div className="glass-card" style={{ marginBottom: '24px', padding: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '12px' }}>
            About RothC Model
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '12px' }}>
            RothC is a model for the turnover of organic carbon in non-waterlogged topsoil.
            It simulates the decomposition of soil organic carbon into five pools:
          </p>
          <ul style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6', paddingLeft: '20px', marginBottom: '12px' }}>
            <li><strong>DPM</strong> - Decomposable Plant Material</li>
            <li><strong>RPM</strong> - Resistant Plant Material</li>
            <li><strong>BIO</strong> - Microbial Biomass</li>
            <li><strong>HUM</strong> - Humified Organic Matter</li>
            <li><strong>IOM</strong> - Inert Organic Matter</li>
          </ul>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
            The model accounts for effects of soil temperature, moisture, and clay content
            on decomposition rates. Reference: Coleman & Jenkinson (1996).
          </p>
        </div>
      )}

      {/* Simulator */}
      <MotorSimulator motor={ROTHC_MOTOR} />

      {/* Scientific Notes */}
      <div className="glass-card" style={{ marginTop: '24px', padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <TrendingUp size={18} style={{ color: 'var(--accent-primary)' }} />
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            Key Equations
          </h3>
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'monospace', lineHeight: '1.8' }}>
          <p>dC/dt = -k × ρ(T) × ξ(w) × C</p>
          <p>where: k = decomposition rate, ρ(T) = temperature factor, ξ(w) = moisture factor</p>
          <p>Temperature factor: ρ(T) = 47.9 / (1 + e^(106/(T+18.3)))</p>
        </div>
      </div>
    </div>
  );
}
