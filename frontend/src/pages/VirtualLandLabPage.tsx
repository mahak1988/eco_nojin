import React, { useState } from 'react';
import {
  Wind,
  Sparkles,
  Play,
  Pause,
  RotateCcw,
  MapPin,
  Sun,
  CloudRain,
  Zap,
  Info,
} from 'lucide-react';
import { AppLayout } from '../components/layout/AppLayout';
import { Card, Button } from '../components/ui';
import { API_BASE_URL } from '../config';
import { VLLTerrain3D } from '../components/vll/VLLTerrain3D';
import { InterventionPanel } from '../components/vll/VLLInterventionPanel';
import { VLLLayerManager } from '../components/vll/VLLLayerManager';
import { VLLResultsBar } from '../components/vll/VLLResultsBar';
import { VLLAIAdvisor } from '../components/vll/VLLAIAdvisor';
import { VLLWeatherControl } from '../components/vll/VLLWeatherControl';
import { RealLandLoader } from '../components/vll/RealLandLoader';
import { ScientificChainPanel } from '../components/hydroma/ScientificChainPanel';
import { ScenarioCompare } from '../components/hydroma/ScenarioCompare';
import { NdviGridCard } from '../components/vll/NdviGridCard';
import type { RealLandResult } from '../types/vll';

export const VirtualLandLabPage: React.FC = () => {
  // State مدیریت
  const [interventions, setInterventions] = useState<any[]>([]);
  const [weather, setWeather] = useState({
    rainfall: 50, // mm/hr
    wind: 12, // m/s
    temperature: 25,
    sunIntensity: 0.8,
  });
  const [activeLayers, setActiveLayers] = useState<Record<string, boolean>>({
    dem: true,
    slope: false,
    soil: false,
    ndvi: true,
    water: false,
    erosion: false,
  });
  const [isSimulating, setIsSimulating] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [showAdvisor, setShowAdvisor] = useState(false);
  const [timeProgress, setTimeProgress] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [realLand, setRealLand] = useState<RealLandResult | null>(null);
  const [coords, setCoords] = useState({ lat: 35.5, lon: 51.5 });
  const [simError, setSimError] = useState<string | null>(null);

  // بارگذاری زمین واقعی (Phase 1): اعمال اقلیم و خاک واقعی روی شبیه‌ساز
  const applyRealLand = (result: RealLandResult) => {
    setRealLand(result);
    setCoords({ lat: result.lat, lon: result.lon });
    const cli = result.climate;
    if (cli?.status === 'ok') {
      setWeather((prev) => ({
        ...prev,
        temperature: cli.latest?.tmax_c ?? cli.avg_temp_c ?? prev.temperature,
        rainfall: Math.max(0, Math.min(150, cli.latest?.precipitation_mm ?? prev.rainfall)),
      }));
    }
  };

  // مداخلات
  const addIntervention = (intv: any) => {
    setInterventions([...interventions, { ...intv, id: Date.now() }]);
  };
  const removeIntervention = (id: number) => {
    setInterventions(interventions.filter((i) => i.id !== id));
  };

  // شبیه‌سازی
  const runSimulation = async () => {
    setIsSimulating(true);
    setSimError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/simulation/comprehensive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          simulation_type: 'comprehensive',
          context: {
            area_ha: 50,
            crop: { crop_type: 'wheat' },
            weather: {
              precipitation_mm: weather.rainfall * 10,
              wind_speed_ms: weather.wind,
            },
            soil: realLand?.soil?.texture
              ? { texture: realLand.soil.texture, organic_carbon_pct: realLand.soil.soc_pct ?? 1.2 }
              : { texture: 'loam', organic_carbon_pct: 1.2 },
            topography: { slope_pct: 10 },
            interventions: interventions.map((i) => ({
              intervention_id: i.id,
              coverage_pct: i.coverage || 100,
              parameters: i.parameters || {},
            })),
          },
        }),
      });
      if (!response.ok) {
        const text = await response.text().catch(() => '');
        throw new Error(`خطای HTTP ${response.status}${text ? `: ${text.slice(0, 200)}` : ''}`);
      }
      const data = await response.json();
      setResults(data);
    } catch (error) {
      // هیچ fallback ساختگی — خطا صادقانه نمایش داده می‌شود (قرارداد W-001)
      console.error('Simulation error:', error);
      setResults(null);
      setSimError(error instanceof Error ? error.message : 'خطا در شبیه‌سازی');
    } finally {
      setIsSimulating(false);
    }
  };

  const resetScenario = () => {
    setInterventions([]);
    setResults(null);
    setTimeProgress(0);
  };

  return (
    <AppLayout>
      <div style={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
        {/* Header Bar */}
        <div
          style={{
            padding: '1rem 2rem',
            background: 'linear-gradient(90deg, var(--color-primary), var(--color-info))',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Sparkles size={28} />
            <div>
              <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>
                🌍 آزمایشگاه مجازی زمین
              </h1>
              <p style={{ margin: 0, fontSize: '0.875rem', opacity: 0.9 }}>
                Virtual Land Laboratory - HyDroMa
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Button
              variant="secondary"
              onClick={resetScenario}
              style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: 'none' }}
            >
              <RotateCcw size={16} /> ریست
            </Button>
            <Button
              variant="secondary"
              onClick={() => setShowAdvisor(!showAdvisor)}
              style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: 'none' }}
            >
              <Zap size={16} /> دستیار AI
            </Button>
            <Button
              variant="primary"
              onClick={runSimulation}
              disabled={isSimulating}
              style={{ background: 'white', color: 'var(--color-primary)' }}
            >
              {isSimulating ? (
                '⏳ شبیه‌سازی...'
              ) : (
                <>
                  <Play size={16} /> اجرای سناریو
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Main Content */}
        <div
          style={{
            flex: 1,
            display: 'grid',
            gridTemplateColumns: '320px 1fr 320px',
            gap: 0,
            overflow: 'hidden',
          }}
        >
          {/* Left Panel: Controls */}
          <div
            style={{
              background: 'var(--color-surface)',
              borderLeft: '1px solid var(--color-border)',
              overflowY: 'auto',
              padding: '1rem',
            }}
          >
            {/* Real Land Loader (Phase 1) */}
            <RealLandLoader onLoaded={applyRealLand} />

            {/* Scientific chain (Phase 3): زنجیره علمی واقعی */}
            <div style={{ marginBottom: '1rem' }}>
              <ScientificChainPanel
                lat={coords.lat}
                lon={coords.lon}
                crop="wheat"
                plantingDate="2024-11-15"
                slopePct={10}
                catchmentKm2={10}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <ScenarioCompare lat={coords.lat} lon={coords.lon} crop="wheat" />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <NdviGridCard satellite={realLand?.satellite} />
            </div>

            {/* Layer Manager */}
            <VLLLayerManager
              activeLayers={activeLayers}
              onToggleLayer={(key) =>
                setActiveLayers({ ...activeLayers, [key]: !activeLayers[key] })
              }
            />

            {/* Weather Control */}
            <VLLWeatherControl weather={weather} onChange={setWeather} />

            {/* Time Control */}
            <Card title="⏱️ کنترل زمان" icon={<Info size={18} />} className="mb-4">
              <div style={{ marginBottom: '0.75rem' }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.875rem',
                    marginBottom: '0.25rem',
                  }}
                >
                  <span>پیشرفت</span>
                  <strong>سال {Math.floor(timeProgress / 12) + 1}</strong>
                </div>
                <input
                  type="range"
                  min="0"
                  max="120"
                  value={timeProgress}
                  onChange={(e) => setTimeProgress(parseInt(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                >
                  {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                </button>
                <button onClick={() => setTimeProgress(0)} className="btn btn-ghost">
                  <RotateCcw size={14} />
                </button>
              </div>
            </Card>
          </div>

          {/* Center: 3D Terrain */}
          <div style={{ position: 'relative', background: '#1a1a2e' }}>
            <VLLTerrain3D
              interventions={interventions}
              weather={weather}
              activeLayers={activeLayers}
              timeProgress={timeProgress}
              isPlaying={isPlaying}
            />

            {/* Floating Info */}
            <div
              style={{
                position: 'absolute',
                top: 20,
                left: 20,
                background: 'rgba(0, 0, 0, 0.7)',
                backdropFilter: 'blur(10px)',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-lg)',
                color: 'white',
                fontSize: '0.875rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
              }}
            >
              <MapPin size={16} color="#22c55e" />
              <div>
                <div style={{ fontWeight: 600 }}>{realLand ? 'زمین واقعی' : 'مزرعه نمونه'}</div>
                <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                  {realLand
                    ? `${realLand.lat.toFixed(3)}°N, ${realLand.lon.toFixed(3)}°E | ۵۰ هکتار`
                    : '۵۰ هکتار | ۳۵.۵°N, ۵۱.۵°E'}
                </div>
              </div>
            </div>

            {/* Real-data indicator */}
            {realLand && (
              <div
                style={{
                  position: 'absolute',
                  top: 20,
                  left: 230,
                  background: realLand.summary.all_real
                    ? 'rgba(34,197,94,0.9)'
                    : 'rgba(245,158,11,0.9)',
                  padding: '0.4rem 0.8rem',
                  borderRadius: 'var(--radius-full)',
                  color: 'white',
                  fontWeight: 700,
                  fontSize: '0.75rem',
                }}
              >
                {realLand.summary.all_real ? '✅ ۱۰۰٪ داده واقعی' : '🔶 داده واقعی (اقلیم+خاک)'}
              </div>
            )}

            {/* Live Weather Indicator */}
            <div
              style={{
                position: 'absolute',
                top: 20,
                right: 20,
                background: 'rgba(0, 0, 0, 0.7)',
                backdropFilter: 'blur(10px)',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-lg)',
                color: 'white',
                fontSize: '0.875rem',
                display: 'flex',
                gap: '1rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CloudRain size={16} color="#3b82f6" />
                <span>{weather.rainfall} mm</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Wind size={16} color="#a3a3a3" />
                <span>{weather.wind} m/s</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sun size={16} color="#fbbf24" />
                <span>{weather.temperature}°C</span>
              </div>
            </div>

            {/* Intervention Counter */}
            <div
              style={{
                position: 'absolute',
                bottom: 20,
                left: 20,
                background: 'rgba(34, 197, 94, 0.9)',
                padding: '0.5rem 1rem',
                borderRadius: 'var(--radius-full)',
                color: 'white',
                fontWeight: 600,
                fontSize: '0.875rem',
              }}
            >
              🛠️ {interventions.length} مداخله فعال
            </div>
          </div>

          {/* Right Panel: Interventions + AI */}
          <div
            style={{
              background: 'var(--color-surface)',
              borderRight: '1px solid var(--color-border)',
              overflowY: 'auto',
              padding: '1rem',
            }}
          >
            {showAdvisor && results && (
              <VLLAIAdvisor
                recommendations={results.recommendations || []}
                onApply={(action) => {
                  addIntervention({ id: action, name: action, coverage: 100 });
                }}
              />
            )}

            <InterventionPanel
              interventions={interventions}
              onAdd={addIntervention}
              onRemove={removeIntervention}
            />
          </div>
        </div>

        {/* Results Bar at bottom */}
        {simError && (
          <div
            style={{
              padding: '0.6rem 2rem',
              background: 'rgba(239,68,68,0.12)',
              borderTop: '1px solid #ef4444',
              color: '#ef4444',
              fontSize: '0.85rem',
            }}
          >
            ⚠️ {simError}
          </div>
        )}
        <VLLResultsBar results={results} isSimulating={isSimulating} />
      </div>
    </AppLayout>
  );
};
