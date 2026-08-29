/**
 * SWAT Model Page - Hydrology Simulation
 * Uses the SWATPlusMotor from scientific_motors
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Droplet, Info, TrendingUp, BookOpen
} from 'lucide-react';
import MotorSimulator from '../components/simulators/MotorSimulator';
import "./admin/AdminTheme.css";

const SWAT_MOTOR = {
  key: 'swat',
  name: 'SWAT+',
  description: 'Soil and Water Assessment Tool - Watershed hydrology simulation',
  category: 'Hydrology',
  parameters: [
    { name: 'watershed_area', type: 'number', default: 100, min: 1, max: 10000, description: 'Watershed area (km²)' },
    { name: 'rainfall', type: 'number', default: 300, min: 50, max: 2000, description: 'Annual rainfall (mm)' },
    { name: 'land_use', type: 'select', options: ['cropland', 'forest', 'grassland', 'urban'], description: 'Primary land use' },
    { name: 'soil_type', type: 'select', options: ['clay', 'loam', 'sand', 'silt'], description: 'Dominant soil type' },
    { name: 'slope', type: 'number', default: 5, min: 0, max: 50, description: 'Average slope (%)' },
    { name: 'curve_number', type: 'number', default: 75, min: 30, max: 100, description: 'SCS curve number' },
  ],
};

export default function SWATModel() {
  const { t } = useTranslation();
  const [showInfo, setShowInfo] = useState(false);

  return (
    <div className="admin-page-container">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Droplet size={32} style={{ color: '#3b82f6' }} />
            {t('nav.swat', 'SWAT+ Model')}
          </h1>
          <p className="page-subtitle">
            {t('simulator.swatDescription', 'Watershed hydrology simulation')}
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
            About SWAT+ Model
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '12px' }}>
            SWAT+ (Soil and Water Assessment Tool Plus) is a river basin scale model
            developed to quantify the impact of land management practices on water,
            sediment, and agricultural chemical yields.
          </p>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '12px' }}>
            Key processes simulated:
          </p>
          <ul style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6', paddingLeft: '20px', marginBottom: '12px' }}>
            <li>Surface runoff (SCS Curve Number method)</li>
            <li>Groundwater recharge and return flow</li>
            <li>Evapotranspiration (Penman-Monteith)</li>
            <li>Sediment yield (MUSLE)</li>
            <li>Nutrient transport (N, P cycles)</li>
          </ul>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
            Reference: Arnold et al. (1998), USDA-ARS
          </p>
        </div>
      )}

      {/* Simulator */}
      <MotorSimulator motor={SWAT_MOTOR} />

      {/* Scientific Notes */}
      <div className="glass-card" style={{ marginTop: '24px', padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <BookOpen size={18} style={{ color: 'var(--accent-info)' }} />
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            Water Balance Equation
          </h3>
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'monospace', lineHeight: '1.8' }}>
          <p>SW_t = SW_0 + Σ(R_day - Q_surf - ET - w_seep - Q_gw)</p>
          <p>where: SW_t = final soil water, SW_0 = initial soil water</p>
          <p>R_day = daily rainfall, Q_surf = surface runoff</p>
          <p>ET = evapotranspiration, w_seep = percolation, Q_gw = groundwater flow</p>
        </div>
      </div>
    </div>
  );
}
