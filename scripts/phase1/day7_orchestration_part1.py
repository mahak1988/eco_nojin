#!/usr/bin/env python3
"""
Phase 1 - Day 7 - Part 1: Create Sidebar & Viewport Components
==============================================================
This script creates all the extracted sub-components that
HydromaCenter orchestrator will compose.

Part 1: Sidebar components (12 files)
Part 2: Viewport components + main orchestration + tests

After both parts run:
- Old HyDroMaCenter.tsx backed up
- New orchestration in place
- Tests passing
- Committed & pushed
"""

import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend" / "src"
HYDROMA = FRONTEND / "features" / "hydroma"
PAGES = FRONTEND / "pages"


def write_file(path: Path, content: str):
    """نوشتن فایل با ایجاد پوشه‌ها"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    lines = len(content.splitlines())
    print(f"  ✓ {path.relative_to(FRONTEND)} ({lines} lines)")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 0: Update useRealDem to use store (single source of truth)
# ═══════════════════════════════════════════════════════════════════════

USE_REAL_DEM_UPDATED = '''/**
 * useRealDem Hook (Store-Based)
 * =============================
 * Loads real DEM data from API and syncs with Zustand store.
 *
 * This version uses the global store as source of truth,
 * ensuring all components see the same terrain/siteMeta state.
 *
 * @module features/hydroma/hooks/useRealDem
 */

import { useCallback, useEffect } from 'react';
import { fetchDemGrid, buildRealTerrain } from '../../../lib/demApi';
import type { DemGrid } from '../../../lib/demApi';
import { useHydromaStore } from '../store';

const DEFAULT_SITE_ID = 'SITE265';
const AUTO_INIT = true;

export interface UseRealDemResult {
  terrain: ReturnType<typeof useHydromaStore.getState>['terrain'];
  siteMeta: ReturnType<typeof useHydromaStore.getState>['siteMeta'];
  loading: boolean;
  error: string;
  loadSite: (siteId: string) => Promise<void>;
  lastClickInfo: string;
}

export function useRealDem(): UseRealDemResult {
  const terrain = useHydromaStore((s) => s.terrain);
  const siteMeta = useHydromaStore((s) => s.siteMeta);
  const demLoading = useHydromaStore((s) => s.demLoading);
  const demError = useHydromaStore((s) => s.demError);
  const lastClickInfo = useHydromaStore((s) => s.lastClickInfo);

  const setTerrain = useHydromaStore((s) => s.setTerrain);
  const setSiteMeta = useHydromaStore((s) => s.setSiteMeta);
  const setDemLoading = useHydromaStore((s) => s.setDemLoading);
  const setDemError = useHydromaStore((s) => s.setDemError);
  const setLastClickInfo = useHydromaStore((s) => s.setLastClickInfo);

  const loadSite = useCallback(
    async (siteId: string) => {
      setDemLoading(true);
      setDemError('');

      try {
        const dem: DemGrid = await fetchDemGrid(siteId);
        const built = buildRealTerrain(dem);

        setTerrain(built);
        setSiteMeta({
          lat: dem.lat,
          lon: dem.lon,
          siteId: dem.site_id,
        });

        const relief = (dem.max_elev - dem.min_elev).toFixed(0);
        setLastClickInfo(`Real DEM loaded: ${dem.site_id} relief=${relief}m`);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setDemError(msg);
      } finally {
        setDemLoading(false);
      }
    },
    [setDemLoading, setDemError, setTerrain, setSiteMeta, setLastClickInfo]
  );

  useEffect(() => {
    if (AUTO_INIT && !terrain && !demLoading && !demError) {
      void loadSite(DEFAULT_SITE_ID);
    }
  }, [terrain, demLoading, demError, loadSite]);

  return {
    terrain,
    siteMeta,
    loading: demLoading,
    error: demError,
    loadSite,
    lastClickInfo,
  };
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 1: Shared Styles
# ═══════════════════════════════════════════════════════════════════════

SIDEBAR_STYLES = '''/**
 * Sidebar Shared Styles
 * ======================
 * Common style objects for sidebar components.
 *
 * @module features/hydroma/components/sidebar/styles
 */

import type { CSSProperties } from 'react';

export const sidebarStyles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    overflowY: 'auto',
    paddingRight: '4px',
  } as CSSProperties,

  section: {
    background: 'rgba(15, 23, 42, 0.9)',
    backdropFilter: 'blur(10px)',
    borderRadius: '12px',
    padding: '12px',
    border: '1px solid rgba(255,255,255,0.1)',
  } as CSSProperties,

  sectionCyan: {
    background: 'rgba(6, 182, 212, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '12px',
    padding: '12px',
    border: '1px solid rgba(6, 182, 212, 0.3)',
    marginBottom: '12px',
  } as CSSProperties,

  label: {
    fontSize: '12px',
    color: 'rgba(255,255,255,0.6)',
    marginBottom: '8px',
    fontWeight: 700,
    textTransform: 'uppercase',
  } as CSSProperties,

  labelInline: {
    fontSize: '11px',
    color: 'rgba(255,255,255,0.7)',
    display: 'block',
    marginBottom: '4px',
  } as CSSProperties,

  button: (active: boolean, activeColor = '#3b82f6') => ({
    padding: '8px 4px',
    borderRadius: '8px',
    background: active ? activeColor : 'rgba(255,255,255,0.05)',
    color: active ? 'white' : 'rgba(255,255,255,0.6)',
    border: active ? 'none' : '1px solid rgba(255,255,255,0.1)',
    cursor: 'pointer',
    fontSize: '11px',
    fontWeight: 600,
  } as CSSProperties),

  toolButton: (active: boolean, color: string) => ({
    padding: '10px 12px',
    borderRadius: '8px',
    background: active ? color : 'rgba(255,255,255,0.03)',
    color: active ? 'white' : 'rgba(255,255,255,0.7)',
    border: active ? 'none' : '1px solid rgba(255,255,255,0.1)',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  } as CSSProperties),

  opButton: (active: boolean) => ({
    padding: '8px 6px',
    borderRadius: '6px',
    background: active ? '#8b5cf6' : 'rgba(255,255,255,0.03)',
    color: active ? 'white' : 'rgba(255,255,255,0.7)',
    border: active ? 'none' : '1px solid rgba(255,255,255,0.1)',
    cursor: 'pointer',
    fontSize: '10px',
    fontWeight: 600,
  } as CSSProperties),

  grid4: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '6px',
  } as CSSProperties,

  grid2: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '6px',
  } as CSSProperties,

  column: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  } as CSSProperties,

  listItem: (color: string) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '6px 8px',
    background: `${color}15`,
    borderRadius: '6px',
    marginBottom: '4px',
    fontSize: '11px',
    border: `1px solid ${color}40`,
  } as CSSProperties),

  deleteButton: {
    padding: '4px 6px',
    borderRadius: '4px',
    background: 'rgba(239, 68, 68, 0.3)',
    color: '#fca5a5',
    border: 'none',
    cursor: 'pointer',
  } as CSSProperties,

  alertBox: (color: string) => ({
    marginTop: '8px',
    padding: '8px',
    background: `${color}26`,
    borderRadius: '6px',
    fontSize: '11px',
    color,
  } as CSSProperties),
} as const;
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 2: ViewModeControls
# ═══════════════════════════════════════════════════════════════════════

VIEW_MODE_CONTROLS = '''/**
 * ViewModeControls
 * =================
 * Camera view preset selector (3D, Top, Side, Section).
 *
 * @module features/hydroma/components/sidebar/ViewModeControls
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore, selectViewMode } from '../../store';
import { VIEW_MODES } from '../../constants';
import { sidebarStyles } from './styles';

export function ViewModeControls() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';
  const viewMode = useHydromaStore(selectViewMode);
  const setViewMode = useHydromaStore((s) => s.setViewMode);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>
        {isFa ? 'حالت نمایش' : 'View Mode'}
      </div>
      <div style={sidebarStyles.grid4}>
        {VIEW_MODES.map((v) => (
          <button
            key={v.id}
            onClick={() => setViewMode(v.id)}
            style={sidebarStyles.button(viewMode === v.id)}
          >
            {isFa ? v.fa : v.label}
          </button>
        ))}
      </div>
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 3: AtmosphereControls
# ═══════════════════════════════════════════════════════════════════════

ATMOSPHERE_CONTROLS = '''/**
 * AtmosphereControls
 * ===================
 * Rain and Camera Tour toggles.
 *
 * @module features/hydroma/components/sidebar/AtmosphereControls
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';
import { sidebarStyles } from './styles';

export function AtmosphereControls() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const rainOn = useHydromaStore((s) => s.climate.rainOn);
  const tourOn = useHydromaStore((s) => s.tourOn);
  const toggleRain = useHydromaStore((s) => s.toggleRain);
  const toggleTour = useHydromaStore((s) => s.toggleTour);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>
        {isFa ? 'اقلیم و دوربین' : 'Atmosphere & Camera'}
      </div>
      <div style={sidebarStyles.grid2}>
        <button
          onClick={toggleRain}
          style={sidebarStyles.button(rainOn, '#0284c7')}
        >
          {isFa ? 'باران' : 'Rain'}
        </button>
        <button
          onClick={toggleTour}
          style={sidebarStyles.button(tourOn, '#7c3aed')}
        >
          {isFa ? 'تور دوربین' : 'Camera Tour'}
        </button>
      </div>
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 4: ToolModeControls
# ═══════════════════════════════════════════════════════════════════════

TOOL_MODE_CONTROLS = '''/**
 * ToolModeControls
 * =================
 * Tool mode selector + contextual UI for draw-polygon and place-op.
 *
 * @module features/hydroma/components/sidebar/ToolModeControls
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';
import { TOOL_MODES, ENGINEERING_OPS } from '../../constants';
import { usePolygonDrawing } from '../../hooks';
import { sidebarStyles } from './styles';

export function ToolModeControls() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const toolMode = useHydromaStore((s) => s.toolMode);
  const selectedOpType = useHydromaStore((s) => s.selectedOpType);
  const setToolMode = useHydromaStore((s) => s.setToolMode);
  const setSelectedOpType = useHydromaStore((s) => s.setSelectedOpType);

  const { finish, cancel, canFinish, pointCount } = usePolygonDrawing(isFa);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>
        {isFa ? 'حالت ابزار' : 'Tool Mode'}
      </div>

      {/* Main tool buttons */}
      <div style={sidebarStyles.column}>
        {TOOL_MODES.map((t) => (
          <button
            key={t.id}
            onClick={() => setToolMode(t.id)}
            style={sidebarStyles.toolButton(toolMode === t.id, t.color)}
          >
            <span style={{ fontSize: '16px' }}>{t.icon}</span>
            <span>{isFa ? t.fa : t.label}</span>
          </button>
        ))}
      </div>

      {/* Draw polygon UI */}
      {toolMode === 'draw-polygon' && (
        <div style={sidebarStyles.alertBox('#fbbf24')}>
          💡 {isFa ? 'روی زمین کلیک کنید (نقاط: ' : 'Click terrain ('}
          {pointCount})
          <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
            <button
              onClick={finish}
              disabled={!canFinish}
              style={{
                flex: 1,
                padding: '6px',
                borderRadius: '4px',
                background: canFinish ? '#f59e0b' : 'rgba(255,255,255,0.1)',
                color: 'white',
                border: 'none',
                cursor: canFinish ? 'pointer' : 'not-allowed',
                fontSize: '11px',
              }}
            >
              ✓ {isFa ? 'اتمام' : 'Finish'}
            </button>
            <button
              onClick={cancel}
              style={{
                flex: 1,
                padding: '6px',
                borderRadius: '4px',
                background: 'rgba(239, 68, 68, 0.2)',
                color: '#fca5a5',
                border: 'none',
                cursor: 'pointer',
                fontSize: '11px',
              }}
            >
              ✕ {isFa ? 'پاک' : 'Clear'}
            </button>
          </div>
        </div>
      )}

      {/* Place operation UI */}
      {toolMode === 'place-op' && (
        <div style={{ marginTop: '8px' }}>
          <div style={{ ...sidebarStyles.labelInline, marginBottom: '4px' }}>
            {isFa ? 'نوع عملیات:' : 'Operation type:'}
          </div>
          <div style={sidebarStyles.grid2}>
            {ENGINEERING_OPS.map((op) => (
              <button
                key={op.id}
                onClick={() => setSelectedOpType(op.id)}
                style={sidebarStyles.opButton(selectedOpType === op.id)}
              >
                <span style={{ fontSize: '14px' }}>{op.emoji}</span>
                <div>{isFa ? op.fa : op.name}</div>
              </button>
            ))}
          </div>
          {selectedOpType && (
            <div
              style={{
                marginTop: '6px',
                padding: '6px',
                background: 'rgba(139, 92, 246, 0.15)',
                borderRadius: '6px',
                fontSize: '11px',
                color: '#c4b5fd',
                textAlign: 'center',
              }}
            >
              ✓ {isFa ? 'روی زمین کلیک کنید' : 'Click on terrain to place'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 5: WindControls
# ═══════════════════════════════════════════════════════════════════════

WIND_CONTROLS = '''/**
 * WindControls
 * =============
 * Wind speed and direction sliders.
 *
 * @module features/hydroma/components/sidebar/WindControls
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';
import { sidebarStyles } from './styles';

export function WindControls() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const windSpeed = useHydromaStore((s) => s.climate.windSpeed);
  const windDirection = useHydromaStore((s) => s.climate.windDirection);
  const setWindSpeed = useHydromaStore((s) => s.setWindSpeed);
  const setWindDirection = useHydromaStore((s) => s.setWindDirection);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>💨 {isFa ? 'باد' : 'Wind'}</div>

      <label style={sidebarStyles.labelInline}>
        {isFa ? 'سرعت' : 'Speed'}: {windSpeed} km/h
      </label>
      <input
        type="range"
        min={0}
        max={100}
        value={windSpeed}
        onChange={(e) => setWindSpeed(parseInt(e.target.value))}
        style={{ width: '100%', accentColor: '#a855f7' }}
      />

      <label style={{ ...sidebarStyles.labelInline, marginTop: '8px' }}>
        {isFa ? 'جهت' : 'Direction'}: {windDirection}°
      </label>
      <input
        type="range"
        min={0}
        max={360}
        value={windDirection}
        onChange={(e) => setWindDirection(parseInt(e.target.value))}
        style={{ width: '100%', accentColor: '#a855f7' }}
      />
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 6: VisualControls
# ═══════════════════════════════════════════════════════════════════════

VISUAL_CONTROLS = '''/**
 * VisualControls
 * ================
 * Decor, growth, crop, and plots management.
 *
 * @module features/hydroma/components/sidebar/VisualControls
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';
import { sidebarStyles } from './styles';

export function VisualControls() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const visual = useHydromaStore((s) => s.visual);
  const plots = useHydromaStore((s) => s.plots);

  const setShowDecor = useHydromaStore((s) => s.setShowDecor);
  const setGrowth = useHydromaStore((s) => s.setGrowth);
  const setCropVisual = useHydromaStore((s) => s.setCropVisual);
  const clearPlots = useHydromaStore((s) => s.clearPlots);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>
        {isFa ? 'نمایش و داده' : 'Visual & Data'}
      </div>

      {/* Decor toggle */}
      <label
        style={{
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
          fontSize: '12px',
          color: 'white',
          marginBottom: '6px',
        }}
      >
        <input
          type="checkbox"
          checked={visual.showDecor}
          onChange={(e) => setShowDecor(e.target.checked)}
        />
        🏡 {isFa ? 'گرافیک مزرعه' : 'Farm decor'}
      </label>

      {/* Growth slider */}
      <label style={sidebarStyles.labelInline}>
        {isFa ? 'رشد' : 'Growth'}: {Math.round(visual.growth * 100)}%
      </label>
      <input
        type="range"
        min={0}
        max={1}
        step={0.05}
        value={visual.growth}
        onChange={(e) => setGrowth(parseFloat(e.target.value))}
        style={{
          width: '100%',
          accentColor: '#2f9e44',
          marginBottom: '8px',
        }}
      />

      {/* Crop selector */}
      <select
        value={visual.cropVisual}
        onChange={(e) => setCropVisual(e.target.value as 'corn' | 'wheat' | 'alfalfa')}
        style={{
          width: '100%',
          padding: '6px',
          borderRadius: 6,
          background: '#1e293b',
          color: 'white',
          border: '1px solid rgba(255,255,255,0.2)',
          marginBottom: '8px',
        }}
      >
        <option value="corn">🌽 {isFa ? 'ذرت' : 'Corn'}</option>
        <option value="wheat">🌾 {isFa ? 'گندم' : 'Wheat'}</option>
        <option value="alfalfa">🌿 {isFa ? 'یونجه' : 'Alfalfa'}</option>
      </select>

      {/* Plots display */}
      <div style={{ ...sidebarStyles.labelInline, marginBottom: '6px' }}>
        {isFa ? `پلات‌های داده: ${plots.length}` : `Data plots: ${plots.length}`}
      </div>

      {plots.slice(-4).reverse().map((p) => (
        <div
          key={p.id}
          style={{
            background: 'rgba(57,255,90,0.08)',
            border: '1px solid rgba(57,255,90,0.3)',
            borderRadius: 8,
            padding: '6px 8px',
            marginBottom: 6,
            fontSize: 10,
            color: 'white',
          }}
        >
          💧 {Math.round(p.data.moisture * 100)}% • 🌿{' '}
          {p.data.ndvi.toFixed(2)} • 📐 {Math.round(p.data.elevation)}m
        </div>
      ))}

      {plots.length > 0 && (
        <button
          onClick={clearPlots}
          style={{
            width: '100%',
            padding: '6px',
            borderRadius: 6,
            border: 'none',
            background: 'rgba(239,68,68,0.2)',
            color: '#fca5a5',
            fontSize: 11,
            cursor: 'pointer',
          }}
        >
          🗑️ {isFa ? 'پاک کردن پلات‌ها' : 'Clear plots'}
        </button>
      )}
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 7: ScientificModelsSection
# ═══════════════════════════════════════════════════════════════════════

SCIENTIFIC_MODELS_SECTION = '''/**
 * ScientificModelsSection
 * ========================
 * Scientific models hub (RUSLE, RothC, AquaCrop, etc).
 *
 * @module features/hydroma/components/sidebar/ScientificModelsSection
 */

import { useTranslation } from 'react-i18next';
import { FlaskConical } from 'lucide-react';
import { ScientificHub } from '../../../../components/simulators/ScientificHub';
import { sidebarStyles } from './styles';

export function ScientificModelsSection() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  return (
    <div style={sidebarStyles.sectionCyan}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '8px',
        }}
      >
        <FlaskConical size={16} color="#06b6d4" />
        <span
          style={{
            fontSize: '12px',
            color: '#06b6d4',
            fontWeight: 700,
            textTransform: 'uppercase',
          }}
        >
          {isFa ? 'مدل‌های علمی واقعی' : 'Real Scientific Models'}
        </span>
      </div>

      <div
        style={{
          fontSize: '10px',
          color: 'rgba(255,255,255,0.6)',
          marginBottom: '10px',
          lineHeight: '1.5',
        }}
      >
        {isFa
          ? 'RUSLE • RothC • AquaCrop • Pywr • HEC-RAS • SWAT+ • NSGA-II'
          : 'Erosion • Carbon • Crop • Water • Flood • Watershed • Optimization'}
      </div>

      <ScientificHub />
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 8: LayersPanel
# ═══════════════════════════════════════════════════════════════════════

LAYERS_PANEL = '''/**
 * LayersPanel
 * ============
 * Terrain layer visibility toggles.
 *
 * @module features/hydroma/components/sidebar/LayersPanel
 */

import { useTranslation } from 'react-i18next';
import { useHydromaStore } from '../../store';
import { LAYERS } from '../../constants';
import type { LayerVisibility } from '../../types';
import { sidebarStyles } from './styles';

export function LayersPanel() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const layers = useHydromaStore((s) => s.layers);
  const showNdvi = useHydromaStore((s) => s.showNdvi);
  const toggleLayer = useHydromaStore((s) => s.toggleLayer);
  const setShowNdvi = useHydromaStore((s) => s.setShowNdvi);

  return (
    <div style={sidebarStyles.section}>
      <div style={sidebarStyles.label}>{isFa ? 'لایه‌ها' : 'Layers'}</div>

      {LAYERS.map((l) => {
        const isActive =
          l.key === 'ndvi' ? showNdvi : (layers[l.key as keyof LayerVisibility] ?? false);

        const handleChange = () => {
          if (l.key === 'ndvi') {
            setShowNdvi(!showNdvi);
          } else {
            toggleLayer(l.key as keyof LayerVisibility);
          }
        };

        return (
          <label
            key={l.key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 8px',
              borderRadius: '6px',
              cursor: 'pointer',
              background: isActive ? `${l.color}20` : 'transparent',
              marginBottom: '4px',
              fontSize: '12px',
            }}
          >
            <input
              type="checkbox"
              checked={isActive}
              onChange={handleChange}
              style={{ accentColor: l.color }}
            />
            <span
              style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: l.color,
              }}
            />
            <span
              style={{
                color: 'white',
                fontWeight: isActive ? 700 : 500,
              }}
            >
              {isFa ? l.fa : l.label}
            </span>
          </label>
        );
      })}
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 9: PlacedOpsList
# ═══════════════════════════════════════════════════════════════════════

PLACED_OPS_LIST = '''/**
 * PlacedOpsList
 * ==============
 * List of placed engineering operations with delete.
 *
 * @module features/hydroma/components/sidebar/PlacedOpsList
 */

import { useTranslation } from 'react-i18next';
import { Trash2 } from 'lucide-react';
import { useHydromaStore } from '../../store';
import { ENGINEERING_OPS } from '../../constants';
import { sidebarStyles } from './styles';

export function PlacedOpsList() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const placedOps = useHydromaStore((s) => s.placedOps);
  const removePlacedOp = useHydromaStore((s) => s.removePlacedOp);

  if (placedOps.length === 0) return null;

  return (
    <div style={sidebarStyles.section}>
      <div style={{ fontSize: '12px', color: '#c4b5fd', marginBottom: '8px', fontWeight: 700 }}>
        📍 {isFa ? `جانمایی (${placedOps.length})` : `Placed (${placedOps.length})`}
      </div>

      {placedOps.map((op) => {
        const opDef = ENGINEERING_OPS.find((o) => o.id === op.type);
        return (
          <div
            key={op.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 8px',
              background: 'rgba(139, 92, 246, 0.1)',
              borderRadius: '6px',
              marginBottom: '4px',
              fontSize: '11px',
              border: '1px solid rgba(139, 92, 246, 0.2)',
            }}
          >
            <span>{opDef?.emoji}</span>
            <span style={{ flex: 1, color: 'white' }}>{op.label}</span>
            <span
              style={{
                color: 'rgba(255,255,255,0.4)',
                fontSize: '9px',
                fontFamily: 'monospace',
              }}
            >
              [{op.x.toFixed(1)},{op.y.toFixed(1)}]
            </span>
            <button
              onClick={() => removePlacedOp(op.id)}
              style={sidebarStyles.deleteButton}
            >
              <Trash2 size={11} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 10: PolygonsList
# ═══════════════════════════════════════════════════════════════════════

POLYGONS_LIST = '''/**
 * PolygonsList
 * =============
 * List of drawn polygons with area and delete.
 *
 * @module features/hydroma/components/sidebar/PolygonsList
 */

import { useTranslation } from 'react-i18next';
import { Trash2, Square } from 'lucide-react';
import { useHydromaStore } from '../../store';
import { sidebarStyles } from './styles';

export function PolygonsList() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const polygons = useHydromaStore((s) => s.polygons);
  const removePolygon = useHydromaStore((s) => s.removePolygon);

  if (polygons.length === 0) return null;

  return (
    <div style={sidebarStyles.section}>
      <div style={{ fontSize: '12px', color: '#86efac', marginBottom: '8px', fontWeight: 700 }}>
        📐 {isFa ? `محدوده‌ها (${polygons.length})` : `Polygons (${polygons.length})`}
      </div>

      {polygons.map((poly) => (
        <div key={poly.id} style={sidebarStyles.listItem(poly.color)}>
          <Square size={12} style={{ color: poly.color }} />
          <span style={{ flex: 1, color: 'white' }}>{poly.name}</span>
          <span style={{ color: 'rgba(255,255,255,0.5)' }}>
            {poly.points.length} pts • {poly.area?.toFixed(0) || 0}m²
          </span>
          <button
            onClick={() => removePolygon(poly.id)}
            style={sidebarStyles.deleteButton}
          >
            <Trash2 size={11} />
          </button>
        </div>
      ))}
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 11: DemStatus
# ═══════════════════════════════════════════════════════════════════════

DEM_STATUS = '''/**
 * DemStatus
 * ==========
 * DEM loading indicator and error display.
 *
 * @module features/hydroma/components/sidebar/DemStatus
 */

import { Loader2 } from 'lucide-react';
import { useHydromaStore } from '../../store';

export function DemStatus() {
  const demLoading = useHydromaStore((s) => s.demLoading);
  const demError = useHydromaStore((s) => s.demError);

  return (
    <>
      {demLoading && (
        <div
          style={{
            fontSize: '11px',
            color: '#81C784',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Loader2 size={12} className="spin" /> در حال دریافت DEM واقعی…
        </div>
      )}

      {demError && (
        <div style={{ fontSize: '11px', color: '#fca5a5' }}>{demError}</div>
      )}
    </>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 12: ErosionEffectPanel
# ═══════════════════════════════════════════════════════════════════════

EROSION_EFFECT_PANEL = '''/**
 * ErosionEffectPanel
 * ===================
 * Displays RUSLE erosion calculation results.
 *
 * @module features/hydroma/components/sidebar/ErosionEffectPanel
 */

import { TrendingUp } from 'lucide-react';
import { useHydromaStore } from '../../store';

export function ErosionEffectPanel() {
  const erosionEffect = useHydromaStore((s) => s.erosionEffect);

  if (!erosionEffect) return null;

  return (
    <div
      style={{
        background: 'rgba(76,175,80,0.12)',
        borderRadius: '12px',
        padding: '12px',
        border: '1px solid rgba(76,175,80,0.3)',
        fontSize: '11.5px',
        color: '#dcefe0',
      }}
    >
      <div
        style={{
          fontWeight: 700,
          marginBottom: 6,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <TrendingUp size={13} color="#4CAF50" /> اثر {erosionEffect.op_fa} — RUSLE واقعی
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>فرسایش قبل:</span>
        <b dir="ltr">{erosionEffect.A_before_t_ha_yr} t/ha/yr</b>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>فرسایش بعد:</span>
        <b style={{ color: '#81C784' }} dir="ltr">
          {erosionEffect.A_after_t_ha_yr} t/ha/yr
        </b>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span>کاهش:</span>
        <b style={{ color: '#4CAF50' }}>{erosionEffect.reduction_pct}٪</b>
      </div>

      <div style={{ marginTop: 6, color: '#B0BEC5' }}>{erosionEffect.note_fa}</div>
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 13: HydromaSidebar (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════

HYDROMA_SIDEBAR = '''/**
 * HydromaSidebar
 * ===============
 * Orchestrates all sidebar panels for HyDroMa Center.
 *
 * @module features/hydroma/components/sidebar/HydromaSidebar
 */

import TerrainBuilder from '../../../../components/simulators/TerrainBuilder';
import RealSiteLoader from '../../../../components/simulators/RealSiteLoader';
import { useHydromaStore } from '../../store';
import { DemStatus } from './DemStatus';
import { ErosionEffectPanel } from './ErosionEffectPanel';
import { ViewModeControls } from './ViewModeControls';
import { AtmosphereControls } from './AtmosphereControls';
import { ToolModeControls } from './ToolModeControls';
import { WindControls } from './WindControls';
import { VisualControls } from './VisualControls';
import { ScientificModelsSection } from './ScientificModelsSection';
import { LayersPanel } from './LayersPanel';
import { PlacedOpsList } from './PlacedOpsList';
import { PolygonsList } from './PolygonsList';
import { sidebarStyles } from './styles';

export function HydromaSidebar() {
  const setTerrain = useHydromaStore((s) => s.setTerrain);
  const setSiteMeta = useHydromaStore((s) => s.setSiteMeta);

  return (
    <div style={sidebarStyles.container}>
      {/* Generators */}
      <TerrainBuilder onGenerate={setTerrain} />
      <RealSiteLoader
        onLoaded={(t, meta) => {
          setTerrain(t);
          setSiteMeta(meta);
        }}
      />

      {/* Status */}
      <DemStatus />
      <ErosionEffectPanel />

      {/* View & Camera */}
      <ViewModeControls />
      <AtmosphereControls />

      {/* Tools */}
      <ToolModeControls />

      {/* Environment */}
      <WindControls />
      <VisualControls />

      {/* Science */}
      <ScientificModelsSection />

      {/* Layers */}
      <LayersPanel />

      {/* Lists */}
      <PlacedOpsList />
      <PolygonsList />
    </div>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# SECTION 14: Sidebar Index
# ═══════════════════════════════════════════════════════════════════════

SIDEBAR_INDEX = '''/**
 * Sidebar Components - Barrel Exports
 */

export * from './HydromaSidebar';
export * from './ViewModeControls';
export * from './AtmosphereControls';
export * from './ToolModeControls';
export * from './WindControls';
export * from './VisualControls';
export * from './ScientificModelsSection';
export * from './LayersPanel';
export * from './PlacedOpsList';
export * from './PolygonsList';
export * from './DemStatus';
export * from './ErosionEffectPanel';
export * from './styles';
'''


# ═══════════════════════════════════════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("  🚀 Phase 1 - Day 7 Part 1: Sidebar Components")
    print("=" * 70 + "\n")

    # Update useRealDem to be store-based
    print("🎣 به‌روزرسانی useRealDem hook...")
    write_file(HYDROMA / "hooks" / "useRealDem.ts", USE_REAL_DEM_UPDATED)
    print()

    # Create sidebar components
    print("📦 ایجاد Sidebar Components...")
    write_file(HYDROMA / "components" / "sidebar" / "styles.ts", SIDEBAR_STYLES)
    write_file(HYDROMA / "components" / "sidebar" / "ViewModeControls.tsx", VIEW_MODE_CONTROLS)
    write_file(HYDROMA / "components" / "sidebar" / "AtmosphereControls.tsx", ATMOSPHERE_CONTROLS)
    write_file(HYDROMA / "components" / "sidebar" / "ToolModeControls.tsx", TOOL_MODE_CONTROLS)
    write_file(HYDROMA / "components" / "sidebar" / "WindControls.tsx", WIND_CONTROLS)
    write_file(HYDROMA / "components" / "sidebar" / "VisualControls.tsx", VISUAL_CONTROLS)
    write_file(HYDROMA / "components" / "sidebar" / "ScientificModelsSection.tsx", SCIENTIFIC_MODELS_SECTION)
    write_file(HYDROMA / "components" / "sidebar" / "LayersPanel.tsx", LAYERS_PANEL)
    write_file(HYDROMA / "components" / "sidebar" / "PlacedOpsList.tsx", PLACED_OPS_LIST)
    write_file(HYDROMA / "components" / "sidebar" / "PolygonsList.tsx", POLYGONS_LIST)
    write_file(HYDROMA / "components" / "sidebar" / "DemStatus.tsx", DEM_STATUS)
    write_file(HYDROMA / "components" / "sidebar" / "ErosionEffectPanel.tsx", EROSION_EFFECT_PANEL)
    write_file(HYDROMA / "components" / "sidebar" / "HydromaSidebar.tsx", HYDROMA_SIDEBAR)
    write_file(HYDROMA / "components" / "sidebar" / "index.ts", SIDEBAR_INDEX)
    print()

    # Summary
    print("=" * 70)
    print("  📊 Summary Part 1")
    print("=" * 70 + "\n")

    print("  Files created:")
    print("    • hooks/useRealDem.ts (updated to use store)")
    print("    • components/sidebar/styles.ts")
    print("    • components/sidebar/ViewModeControls.tsx")
    print("    • components/sidebar/AtmosphereControls.tsx")
    print("    • components/sidebar/ToolModeControls.tsx")
    print("    • components/sidebar/WindControls.tsx")
    print("    • components/sidebar/VisualControls.tsx")
    print("    • components/sidebar/ScientificModelsSection.tsx")
    print("    • components/sidebar/LayersPanel.tsx")
    print("    • components/sidebar/PlacedOpsList.tsx")
    print("    • components/sidebar/PolygonsList.tsx")
    print("    • components/sidebar/DemStatus.tsx")
    print("    • components/sidebar/ErosionEffectPanel.tsx")
    print("    • components/sidebar/HydromaSidebar.tsx (orchestrator)")
    print("    • components/sidebar/index.ts")
    print()

    print("  Next: Run day7_orchestration_part2.py")
    print("    • Create Viewport components")
    print("    • Create new HyDroMaCenter.tsx orchestration")
    print("    • Fix useEsriTexture test")
    print("    • Backup old file, commit & push")
    print()


if __name__ == "__main__":
    main()