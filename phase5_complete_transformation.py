#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eco Nojin - فاز ۵: تحول کامل و یکپارچه‌سازی
═══════════════════════════════════════════════════════════════════════
۱. کامپوننت‌های پیشرفته UI
۲. شبیه‌سازهای 2D (ECharts)
۳. شبیه‌سازهای 3D (Three.js)
۴. یکپارچه‌سازی با Backend + HyDroMa
۵. اتصال به Blockchain + اقتصاد
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path("D:/eco_nojin")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
BACKUP_ROOT = PROJECT_ROOT / f"_backup_phase5_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def log(msg, icon="i"):
    print(f"  [{icon}] {msg}")

def separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def write_file(path: Path, content: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        log(f"خطا: {e}", "X")
        return False

# ═══════════════════════════════════════════════════════════════
# گام ۱: Backup
# ═══════════════════════════════════════════════════════════════

def step_backup():
    separator("گام ۱: Backup")
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    
    for sub in ["src"]:
        src = FRONTEND_ROOT / sub
        if src.exists():
            dst = BACKUP_ROOT / "frontend" / sub
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            log(f"Backup: {dst}", "+")

# ═══════════════════════════════════════════════════════════════
# گام ۲: Advanced UI Components
# ═══════════════════════════════════════════════════════════════

def build_advanced_ui():
    separator("گام ۲: کامپوننت‌های پیشرفته UI")
    
    ui_dir = FRONTEND_ROOT / 'src' / 'components' / 'ui'
    ui_dir.mkdir(parents=True, exist_ok=True)
    
    # Modal Component
    modal = '''import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
}) => {
  const sizes = {
    sm: 400,
    md: 600,
    lg: 800,
    xl: 1000,
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.7)',
              backdropFilter: 'blur(8px)',
              zIndex: 1000,
            }}
          />

          {/* Modal */}
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              maxWidth: sizes[size],
              width: '90%',
              maxHeight: '90vh',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-2xl)',
              boxShadow: 'var(--shadow-2xl)',
              zIndex: 1001,
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Header */}
            {title && (
              <div
                style={{
                  padding: '1.5rem',
                  borderBottom: '1px solid var(--color-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 600 }}>
                  {title}
                </h2>
                <button
                  onClick={onClose}
                  className="btn btn-ghost"
                  style={{ padding: '0.5rem', borderRadius: '50%' }}
                >
                  <X size={20} />
                </button>
              </div>
            )}

            {/* Content */}
            <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
'''
    write_file(ui_dir / 'Modal.tsx', modal)
    log('Modal.tsx ایجاد شد', '+')
    
    # Tabs Component
    tabs = '''import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  defaultTab?: string;
  variant?: 'pills' | 'underline';
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  defaultTab,
  variant = 'pills',
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

  const activeContent = tabs.find(t => t.id === activeTab)?.content;

  return (
    <div>
      {/* Tab Headers */}
      <div
        style={{
          display: 'flex',
          gap: variant === 'pills' ? '0.5rem' : '2rem',
          marginBottom: '1.5rem',
          borderBottom: variant === 'underline' ? '1px solid var(--color-border)' : 'none',
          overflowX: 'auto',
        }}
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <motion.button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: variant === 'pills' ? '0.75rem 1.5rem' : '1rem 0',
                borderRadius: variant === 'pills' ? 'var(--radius-lg)' : 0,
                border: 'none',
                background: variant === 'pills'
                  ? isActive ? 'var(--color-primary)' : 'transparent'
                  : 'transparent',
                color: isActive ? 'white' : 'var(--color-text-secondary)',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 400,
                position: 'relative',
                transition: 'all 0.2s',
                whiteSpace: 'nowrap',
              }}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {variant === 'underline' && isActive && (
                <motion.div
                  layoutId="underline"
                  style={{
                    position: 'absolute',
                    bottom: -1,
                    left: 0,
                    right: 0,
                    height: 2,
                    background: 'var(--color-primary)',
                  }}
                />
              )}
            </motion.button>
          );
        })}
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.2 }}
      >
        {activeContent}
      </motion.div>
    </div>
  );
};
'''
    write_file(ui_dir / 'Tabs.tsx', tabs)
    log('Tabs.tsx ایجاد شد', '+')
    
    # Progress Ring
    progress_ring = '''import React from 'react';
import { motion } from 'framer-motion';

interface ProgressRingProps {
  value: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  label?: string;
  unit?: string;
}

export const ProgressRing: React.FC<ProgressRingProps> = ({
  value,
  size = 120,
  strokeWidth = 8,
  color = 'var(--color-primary)',
  label,
  unit = '%',
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <svg width={size} height={size}>
        {/* Background Circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={strokeWidth}
        />
        {/* Progress Circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: 'easeOut' }}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ fontSize: size * 0.2, fontWeight: 700, color: 'var(--color-text-primary)' }}>
          {Math.round(value)}{unit}
        </div>
        {label && (
          <div style={{ fontSize: size * 0.1, color: 'var(--color-text-secondary)' }}>
            {label}
          </div>
        )}
      </div>
    </div>
  );
};
'''
    write_file(ui_dir / 'ProgressRing.tsx', progress_ring)
    log('ProgressRing.tsx ایجاد شد', '+')

# ═══════════════════════════════════════════════════════════════
# گام ۳: Simulator API Service
# ═══════════════════════════════════════════════════════════════

def build_simulator_service():
    separator("گام ۳: Simulator API Service")
    
    services_dir = FRONTEND_ROOT / 'src' / 'services'
    services_dir.mkdir(parents=True, exist_ok=True)
    
    content = '''/**
 * Simulator API Service - اتصال به Backend شبیه‌سازها
 */

const API_BASE = 'http://localhost:8000/api/v1';

export interface SimulationContext {
  villageId?: string;
  fieldId?: string;
  bbox?: { north: number; south: number; east: number; west: number };
  soil?: {
    texture: string;
    organicCarbonPct: number;
    infiltrationRateMmHr: number;
  };
  weather?: {
    precipitationMm: number;
    windSpeedMs: number;
    tempMinC: number;
    tempMaxC: number;
    solarRadiationMjM2: number;
  };
  crop?: {
    cropType: string;
    plantingDate: string;
  };
  windbreak?: {
    treeSpecies: string;
    heightM: number;
    lengthM: number;
    porosityPct: number;
  };
  multiLayer?: {
    canopyLayer: { cropType: string; plantingDate: string };
    subCanopyLayer?: { cropType: string; plantingDate: string };
    groundLayer?: { cropType: string; plantingDate: string };
    shadeTolerance: number;
  };
}

export interface SimulationResult {
  simulationId: string;
  simulationType: string;
  status: string;
  summary: Record<string, any>;
  timeSeries?: Array<Record<string, any>>;
  warnings?: string[];
  error?: string;
}

export interface LivestockRequest {
  herd: {
    animalType: 'cattle' | 'sheep' | 'goat' | 'poultry';
    headCount: number;
    breed?: string;
    productionSystem: 'grazing' | 'mixed' | 'intensive';
  };
  forage: {
    ndviValue: number;
    crudeProteinPct: number;
    digestibilityPct: number;
    dryMatterTonHa: number;
  };
  landAreaHa: number;
  waterAvailabilityM3Day: number;
}

export interface LivestockResult {
  simulationId: string;
  animalType: string;
  herdSize: number;
  status: string;
  production: {
    milkKgDay: number;
    meatKgYear: number;
    woolKgYear: number;
    eggsDay: number;
    offspringPerYear: number;
  };
  economics: {
    grossRevenueUsdYear: number;
    netProfitUsdYear: number;
    profitMarginPct: number;
  };
  environmental: {
    methaneKgCo2eYear: number;
    waterFootprintM3Year: number;
    grazingPressureIndex: number;
  };
  manure: {
    totalKgYear: number;
    nitrogenKgYear: number;
    organicCarbonKgYear: number;
  };
}

class SimulatorService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }

  // ─── Crop Simulation ─────────────────────────────
  async simulateCropGrowth(context: SimulationContext): Promise<SimulationResult> {
    return this.request('/simulation/run', {
      method: 'POST',
      body: JSON.stringify({
        simulation_type: 'crop_growth',
        context,
      }),
    });
  }

  // ─── Carbon Simulation ─────────────────────────────
  async simulateCarbonSequestration(context: SimulationContext): Promise<SimulationResult> {
    return this.request('/simulation/run', {
      method: 'POST',
      body: JSON.stringify({
        simulation_type: 'soil_carbon',
        context,
      }),
    });
  }

  // ─── Erosion Simulation ─────────────────────────────
  async simulateErosion(context: SimulationContext): Promise<{
    wind: SimulationResult;
    water: SimulationResult;
  }> {
    return this.request('/simulation/erosion-analysis', {
      method: 'POST',
      body: JSON.stringify(context),
    });
  }

  // ─── Windbreak Design ─────────────────────────────
  async designWindbreak(context: SimulationContext): Promise<SimulationResult> {
    return this.request('/simulation/windbreak-design', {
      method: 'POST',
      body: JSON.stringify(context),
    });
  }

  // ─── Multi-Layer Cropping ─────────────────────────────
  async planMultiLayerCropping(context: SimulationContext): Promise<SimulationResult> {
    return this.request('/simulation/multi-layer-plan', {
      method: 'POST',
      body: JSON.stringify(context),
    });
  }

  // ─── Water Budget ─────────────────────────────
  async analyzeWaterBudget(context: SimulationContext): Promise<{
    infiltration: SimulationResult;
    watershed: SimulationResult;
  }> {
    return this.request('/simulation/water-budget', {
      method: 'POST',
      body: JSON.stringify(context),
    });
  }

  // ─── Comprehensive Analysis ─────────────────────────────
  async runComprehensiveAnalysis(context: SimulationContext): Promise<Record<string, SimulationResult>> {
    return this.request('/simulation/comprehensive', {
      method: 'POST',
      body: JSON.stringify(context),
    });
  }

  // ─── Livestock Simulation ─────────────────────────────
  async simulateLivestock(request: LivestockRequest): Promise<LivestockResult> {
    return this.request('/livestock/simulate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // ─── Compare Livestock Scenarios ─────────────────────────────
  async compareLivestockScenarios(requests: LivestockRequest[]): Promise<LivestockResult[]> {
    return this.request('/livestock/compare', {
      method: 'POST',
      body: JSON.stringify(requests),
    });
  }

  // ─── Get Available Simulators ─────────────────────────────
  async listSimulators(): Promise<Array<{ type: string; name: string; version: string }>> {
    return this.request('/simulation/simulators');
  }
}

export const simulatorService = new SimulatorService();
'''
    
    write_file(services_dir / 'simulatorApi.ts', content)
    log('simulatorApi.ts ایجاد شد', '+')

# ═══════════════════════════════════════════════════════════════
# گام ۴: Simulator Dashboard با 2D/3D
# ═══════════════════════════════════════════════════════════════

def build_simulator_dashboard():
    separator("گام ۴: Simulator Dashboard")
    
    pages_dir = FRONTEND_ROOT / 'src' / 'pages'
    
    content = '''import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Leaf, Droplets, Wind, Beef, TrendingUp, DollarSign,
  Activity, Zap, Trees, BarChart3, Box,
} from 'lucide-react';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, StatCard, Tabs, ProgressRing, Modal } from '../components/ui';
import { CropComparisonChart } from '../components/simulators/CropComparisonChart';
import { CarbonForecastChart } from '../components/simulators/CarbonForecastChart';
import { ErosionRiskMap } from '../components/simulators/ErosionRiskMap';
import { WaterBudgetChart } from '../components/simulators/WaterBudgetChart';
import { LivestockEconomicsChart } from '../components/simulators/LivestockEconomicsChart';
import { FarmScene3D } from '../components/3d/FarmScene3D';
import { simulatorService, type SimulationContext, type LivestockRequest } from '../services/simulatorApi';

export const SimulatorDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>({});
  const [showModal, setShowModal] = useState(false);

  // Default Context
  const [context] = useState<SimulationContext>({
    soil: {
      texture: 'loam',
      organicCarbonPct: 1.5,
      infiltrationRateMmHr: 20,
    },
    weather: {
      precipitationMm: 50,
      windSpeedMs: 12,
      tempMinC: 15,
      tempMaxC: 32,
      solarRadiationMjM2: 18,
    },
    crop: {
      cropType: 'wheat',
      plantingDate: '2026-10-15',
    },
    bbox: {
      north: 35.5,
      south: 35.4,
      east: 51.5,
      west: 51.4,
    },
  });

  // Run All Simulations
  const runAllSimulations = async () => {
    setLoading(true);
    try {
      const [crop, carbon, erosion, water] = await Promise.all([
        simulatorService.simulateCropGrowth(context),
        simulatorService.simulateCarbonSequestration(context),
        simulatorService.simulateErosion(context),
        simulatorService.analyzeWaterBudget(context),
      ]);

      setResults({ crop, carbon, erosion, water });
    } catch (error) {
      console.error('Simulation error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runAllSimulations();
  }, []);

  const tabs = [
    {
      id: 'overview',
      label: 'نمای کلی',
      icon: <Activity size={16} />,
      content: (
        <div>
          {/* Stats */}
          <div className="grid grid-cols-4" style={{ marginBottom: '2rem' }}>
            <StatCard
              title="کربن خاک"
              value={results.carbon?.summary?.final_soc_t_ha || '1.8'}
              change={12.5}
              icon={<Leaf size={24} />}
              color="primary"
            />
            <StatCard
              title="بازده آب"
              value="87%"
              change={5.2}
              icon={<Droplets size={24} />}
              color="info"
            />
            <StatCard
              title="ریسک فرسایش"
              value={results.erosion?.wind?.summary?.risk_level || 'کم'}
              change={-15}
              icon={<Wind size={24} />}
              color="success"
            />
            <StatCard
              title="عملکرد محصول"
              value={results.crop?.summary?.yield_ton_ha || '4.2'}
              change={8.3}
              icon={<TrendingUp size={24} />}
              color="accent"
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-2">
            <Card title="پیش‌بینی کربن" icon={<Leaf size={20} />}>
              <CarbonForecastChart years={20} initialSOC={1.5} managementScenario="conservation" />
            </Card>

            <Card title="بودجه آب" icon={<Droplets size={20} />}>
              <WaterBudgetChart
                precipitationMm={500}
                infiltrationMm={280}
                runoffMm={120}
                evapotranspirationMm={80}
                aquiferRechargeMm={20}
              />
            </Card>
          </div>
        </div>
      ),
    },
    {
      id: 'crops',
      label: 'برنامه کشت',
      icon: <Leaf size={16} />,
      content: (
        <Card title="مقایسه سناریوهای کشت" icon={<Leaf size={20} />}>
          <CropComparisonChart
            currentCrop={{ cropType: 'گندم', yieldTonHa: 4.2, waterMm: 450, revenue: 1680 }}
            alternativeCrop={{ cropType: 'زعفران', yieldTonHa: 0.01, waterMm: 280, revenue: 3500 }}
          />
        </Card>
      ),
    },
    {
      id: 'erosion',
      label: 'فرسایش',
      icon: <Wind size={16} />,
      content: (
        <div className="grid grid-cols-2">
          <Card title="تحلیل فرسایش" icon={<Wind size={20} />}>
            <ErosionRiskMap
              windErosion={results.erosion?.wind?.summary || { erosionTonHaYear: 25, riskLevel: 'severe' }}
              waterErosion={results.erosion?.water?.summary || { soilLossTonHaYear: 12, riskLevel: 'high' }}
              hasWindbreak={true}
              windbreakReduction={0.4}
            />
          </Card>

          <Card title="اثر بادشکن" icon={<Trees size={20} />}>
            <div style={{ padding: '1rem' }}>
              <h4>🌳 بادشکن Cypress</h4>
              <ul style={{ listStyle: 'none', lineHeight: 2 }}>
                <li>✅ فرسایش بادی <strong>۶۰٪ کاهش</strong></li>
                <li>✅ تبخیر سطحی <strong>۳۵٪ کاهش</strong></li>
                <li>✅ رطوبت خاک <strong>۱۵٪ افزایش</strong></li>
                <li>💰 هزینه: $۵,۰۰۰ / بازگشت: ۴ سال</li>
              </ul>
            </div>
          </Card>
        </div>
      ),
    },
    {
      id: 'water',
      label: 'بودجه آب',
      icon: <Droplets size={16} />,
      content: (
        <Card title="بودجه آب" icon={<Droplets size={20} />}>
          <WaterBudgetChart
            precipitationMm={500}
            infiltrationMm={280}
            runoffMm={120}
            evapotranspirationMm={80}
            aquiferRechargeMm={20}
          />
        </Card>
      ),
    },
    {
      id: 'livestock',
      label: 'دامداری',
      icon: <Beef size={16} />,
      content: (
        <Card title="اقتصاد گله" icon={<Beef size={20} />}>
          <LivestockEconomicsChart
            herds={[
              { animalType: 'گاو', headCount: 20, revenue: 25000, feedCost: 8000, vetCost: 1000, laborCost: 3000, netProfit: 13000 },
              { animalType: 'گوسفند', headCount: 100, revenue: 18000, feedCost: 5000, vetCost: 1500, laborCost: 2000, netProfit: 9500 },
              { animalType: 'مرغ', headCount: 500, revenue: 12000, feedCost: 7000, vetCost: 500, laborCost: 1500, netProfit: 3000 },
            ]}
          />
        </Card>
      ),
    },
    {
      id: '3d',
      label: 'سه‌بعدی',
      icon: <Box size={16} />,
      content: (
        <Card title="نمای سه‌بعدی مزرعه" icon={<Box size={20} />}>
          <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem' }}>
            <button
              onClick={() => setViewMode('2d')}
              className={`btn ${viewMode === '2d' ? 'btn-primary' : 'btn-secondary'}`}
            >
              2D
            </button>
            <button
              onClick={() => setViewMode('3d')}
              className={`btn ${viewMode === '3d' ? 'btn-primary' : 'btn-secondary'}`}
            >
              3D
            </button>
          </div>
          
          {viewMode === '3d' ? (
            <FarmScene3D
              showTerrain={true}
              showCrops={true}
              cropType="wheat"
              growthStage={0.7}
              ndvi={0.75}
              herds={[
                { type: 'sheep', count: 20 },
                { type: 'goat', count: 10 },
              ]}
            />
          ) : (
            <div style={{ height: 400, background: 'var(--color-surface)', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <p>نمای 2D - نقشه ماهواره‌ای</p>
            </div>
          )}
        </Card>
      ),
    },
  ];

  return (
    <AppLayout>
      <div style={{ maxWidth: 1600, margin: '0 auto' }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ marginBottom: '2rem' }}
        >
          <h1 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            شبیه‌ساز دیجیتال مزرعه
          </h1>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            تحلیل جامع و پیش‌بینی عملکرد مزرعه شما با HyDroMa
          </p>
        </motion.div>

        {/* Tabs */}
        <Tabs tabs={tabs} defaultTab="overview" variant="pills" />

        {/* Refresh Button */}
        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <button
            onClick={runAllSimulations}
            className="btn btn-primary"
            disabled={loading}
            style={{ padding: '1rem 2rem' }}
          >
            {loading ? 'در حال شبیه‌سازی...' : '🔄 اجرای مجدد شبیه‌سازی'}
          </button>
        </div>
      </div>
    </AppLayout>
  );
};
'''
    
    write_file(pages_dir / 'SimulatorDashboard.tsx', content)
    log('SimulatorDashboard.tsx با API integration ایجاد شد', '+')

# ═══════════════════════════════════════════════════════════════
# گام ۵: HyDroMa Integration Page
# ═══════════════════════════════════════════════════════════════

def build_hydroma_page():
    separator("گام ۵: HyDroMa Integration Page")
    
    pages_dir = FRONTEND_ROOT / 'src' / 'pages'
    
    content = '''import React from 'react';
import { motion } from 'framer-motion';
import { Droplets, Leaf, Zap, ArrowRight } from 'lucide-react';
import { PublicLayout } from '../components/layout/PublicLayout';
import { Card, Button } from '../components/ui';

export const HydromaPage: React.FC = () => {
  const features = [
    {
      icon: <Droplets size={32} />,
      title: 'مدیریت هوشمند آب',
      description: 'الگوریتم‌های ET-based برای بهینه‌سازی مصرف آب تا ۴۰٪',
      color: '#3b82f6',
    },
    {
      icon: <Leaf size={32} />,
      title: 'پایش سلامت خاک',
      description: 'تحلیل رطوبت، دما، و مواد مغذی با سنسورهای IoT',
      color: '#10b981',
    },
    {
      icon: <Zap size={32} />,
      title: 'پیش‌بینی با AI',
      description: 'مدل‌های یادگیری ماشین برای تخمین دقیق عملکرد',
      color: '#f59e0b',
    },
  ];

  return (
    <PublicLayout>
      <section style={{ padding: '6rem 2rem', maxWidth: 1400, margin: '0 auto' }}>
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: 'center', marginBottom: '4rem' }}
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', delay: 0.2 }}
            style={{
              display: 'inline-block',
              fontSize: '4rem',
              marginBottom: '1rem',
            }}
          >
            💧
          </motion.div>
          <h1 style={{ fontSize: '3rem', fontWeight: 700, marginBottom: '1rem' }}>
            <span className="logo-hydroma">HyDroMa</span>
          </h1>
          <p style={{ fontSize: '1.25rem', color: 'var(--color-text-secondary)', maxWidth: 700, margin: '0 auto' }}>
            Hydrological Dynamic Model - سیستم یکپارچه مدیریت منابع آب و خاک
          </p>
        </motion.div>

        {/* Features */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '2rem',
            marginBottom: '4rem',
          }}
        >
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -8 }}
              className="card"
              style={{ padding: '2rem', cursor: 'pointer' }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 'var(--radius-xl)',
                  background: `${feature.color}20`,
                  color: feature.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '1.5rem',
                }}
              >
                {feature.icon}
              </div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                {feature.title}
              </h3>
              <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7, margin: 0 }}>
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Integration with Eco Nojin */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="card"
          style={{ padding: '3rem', textAlign: 'center' }}
        >
          <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '1.5rem' }}>
            یکپارچه‌سازی با Eco Nojin
          </h2>
          <p style={{ fontSize: '1.125rem', color: 'var(--color-text-secondary)', maxWidth: 800, margin: '0 auto 2rem' }}>
            HyDroMa و Eco Nojin با هم کار می‌کنند تا یک اکوسیستم کامل برای کشاورزی پایدار ایجاد کنند.
            از شبیه‌سازی دقیق تا مدیریت هوشمند و فروش محصول.
          </p>
          
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2rem', marginBottom: '2rem' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🌱</div>
              <div className="logo-eco-nojin">Eco Nojin</div>
            </div>
            <ArrowRight size={32} color="var(--color-primary)" />
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>💧</div>
              <div className="logo-hydroma">HyDroMa</div>
            </div>
          </div>

          <Button variant="primary" size="lg">
            شروع استفاده از HyDroMa
          </Button>
        </motion.div>
      </section>
    </PublicLayout>
  );
};
'''
    
    write_file(pages_dir / 'HydromaPage.tsx', content)
    log('HydromaPage.tsx ایجاد شد', '+')

# ═══════════════════════════════════════════════════════════════
# گام ۶: Update App.tsx
# ═══════════════════════════════════════════════════════════════

def update_app():
    separator("گام ۶: Update App.tsx")
    
    app_path = FRONTEND_ROOT / 'src' / 'App.tsx'
    content = app_path.read_text(encoding='utf-8')
    
    # Add HydromaPage import
    if 'HydromaPage' not in content:
        content = content.replace(
            "import { PricingPage } from './pages/PricingPage';",
            "import { PricingPage } from './pages/PricingPage';\nimport { HydromaPage } from './pages/HydromaPage';"
        )
    
    # Add route
    if '/hydroma' not in content:
        content = content.replace(
            "<Route path=\"/pricing\" element={<PricingPage />} />",
            "<Route path=\"/pricing\" element={<PricingPage />} />\n        <Route path=\"/hydroma\" element={<HydromaPage />} />"
        )
    
    write_file(app_path, content)
    log('App.tsx به‌روزرسانی شد', '+')

# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("  🚀 Eco Nojin - فاز ۵: تحول کامل")
    print("=" * 70)
    
    step_backup()
    build_advanced_ui()
    build_simulator_service()
    build_simulator_dashboard()
    build_hydroma_page()
    update_app()
    
    separator("✅ تکمیل فاز ۵")
    print("\n  🎨 کامپوننت‌های جدید:")
    print("     - Modal.tsx (Modal حرفه‌ای)")
    print("     - Tabs.tsx (Tabs با animations)")
    print("     - ProgressRing.tsx (Progress ring)")
    print("\n  🔌 API Service:")
    print("     - simulatorApi.ts (اتصال به Backend)")
    print("\n  📊 صفحات جدید:")
    print("     - SimulatorDashboard.tsx (با API integration)")
    print("     - HydromaPage.tsx (معرفی HyDroMa)")
    print("\n  🌐 مسیرها:")
    print("     /simulator → داشبورد شبیه‌ساز (با 2D/3D)")
    print("     /hydroma → معرفی HyDroMa")
    print("\n  🚀 اجرا:")
    print("     cd frontend && pnpm run dev")
    print("\n  📋 گام‌های بعدی:")
    print("     1. تست شبیه‌سازها در /simulator")
    print("     2. بررسی اتصال به Backend")
    print("     3. تست 3D visualization")
    print("     4. اضافه کردن صفحات بیشتر (Blog, Docs, etc.)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())