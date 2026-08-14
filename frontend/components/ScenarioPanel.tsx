'use client';
import { useState } from 'react';
import { useI18n } from '../lib/i18n-context';
import { API_BASE } from '../lib/config';

interface ScenarioResult {
  scenario_name: string;
  crop: string;
  yield_kg_ha: number;
  revenue_usd_ha: number;
  water_use_mm: number;
  water_productivity: number;
  yield_reduction_pct: number;
}

export default function ScenarioPanel() {
  const { t } = useI18n();
  const [results, setResults] = useState<ScenarioResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Scenario parameters
  const [sspScenario, setSspScenario] = useState('SSP2-4.5');
  const [timeHorizon, setTimeHorizon] = useState(2050);
  const [cropType, setCropType] = useState('wheat');
  const [baselineWater, setBaselineWater] = useState(300);
  const [baselineTemp, setBaselineTemp] = useState(18);

  const runClimateTransition = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/scenarios/whatif/climate-transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario: sspScenario,
          time_horizon: timeHorizon,
          baseline_temp: baselineTemp,
          baseline_precip: baselineWater,
        }),
      });

      if (!res.ok) throw new Error('Scenario analysis failed');
      const data = await res.json();
      setResults(data.scenarios || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const compareCrops = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/scenarios/crop/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop_type: cropType,
          available_water: baselineWater,
          mean_temp: baselineTemp,
        }),
      });

      if (!res.ok) throw new Error('Crop comparison failed');
      const data = await res.json();

      // Convert to scenario format
      const scenarios = Object.entries(data.details || {}).map(([name, detail]: [string, any]) => ({
        scenario_name: name,
        crop: detail.crop,
        yield_kg_ha: detail.actual_yield_kg_ha,
        revenue_usd_ha: detail.gross_revenue_usd_ha,
        water_use_mm: baselineWater,
        water_productivity: detail.system_water_productivity,
        yield_reduction_pct: detail.yield_reduction_pct,
      }));

      setResults(scenarios);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const maxYield = Math.max(...results.map(r => r.yield_kg_ha), 1);
  const maxRevenue = Math.max(...results.map(r => r.revenue_usd_ha), 1);

  return (
    <section
      aria-labelledby="scenario-panel-title"
      style={{
        marginTop: '32px',
        padding: '24px',
        border: '1px solid #ddd',
        borderRadius: '12px',
        background: '#fef3c7',
      }}
    >
      <h2 id="scenario-panel-title" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px', color: '#92400e' }}>
        📊 {t('scenario_title')}
      </h2>

      {/* Parameters */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        <div>
          <label htmlFor="scn-ssp" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('ssp_scenario')}</label>
          <select
            id="scn-ssp"
            value={sspScenario}
            onChange={(e) => setSspScenario(e.target.value)}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          >
            <option value="SSP1-2.6">SSP1-2.6 (Sustainable)</option>
            <option value="SSP2-4.5">SSP2-4.5 (Middle)</option>
            <option value="SSP5-8.5">SSP5-8.5 (Fossil)</option>
          </select>
        </div>

        <div>
          <label htmlFor="scn-horizon" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>{t('time_horizon')}</label>
          <select
            id="scn-horizon"
            value={timeHorizon}
            onChange={(e) => setTimeHorizon(parseInt(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          >
            <option value={2030}>2030</option>
            <option value={2050}>2050</option>
            <option value={2100}>2100</option>
          </select>
        </div>

        <div>
          <label htmlFor="scn-crop" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>Crop Type</label>
          <select
            id="scn-crop"
            value={cropType}
            onChange={(e) => setCropType(e.target.value)}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          >
            <option value="wheat">Wheat</option>
            <option value="barley">Barley</option>
            <option value="corn">Corn</option>
            <option value="millet">Millet</option>
            <option value="sorghum">Sorghum</option>
            <option value="chickpea">Chickpea</option>
            <option value="medicinal_herbs">Medicinal Herbs</option>
          </select>
        </div>

        <div>
          <label htmlFor="scn-water" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>Water (mm)</label>
          <input
            id="scn-water"
            type="number"
            value={baselineWater}
            onChange={(e) => setBaselineWater(parseFloat(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          />
        </div>

        <div>
          <label htmlFor="scn-temp" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '4px' }}>Temp (°C)</label>
          <input
            id="scn-temp"
            type="number"
            value={baselineTemp}
            onChange={(e) => setBaselineTemp(parseFloat(e.target.value))}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '6px' }}
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button
          onClick={runClimateTransition}
          disabled={loading}
          aria-busy={loading}
          style={{ padding: '10px 20px', background: '#92400e', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
        >
          🌡️ {t('climate_transition')}
        </button>
        <button
          onClick={compareCrops}
          disabled={loading}
          aria-busy={loading}
          style={{ padding: '10px 20px', background: '#0369a1', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
        >
          🌾 {t('compare_crops')}
        </button>
      </div>

      {error && <p role="alert" style={{ color: '#dc2626' }}>{t('error_label')}: {error}</p>}
      {loading && <p aria-live="polite" style={{ color: '#92400e' }}>{t('analyzing')}</p>}

      {/* Results */}
      {results.length > 0 && (
        <div aria-live="polite" style={{ background: 'white', padding: '16px', borderRadius: '8px', marginTop: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '12px' }}>{t('results')}</h3>

          {/* Bar Chart */}
          <div style={{ marginBottom: '16px' }}>
            {results.map((r, idx) => (
              <div key={idx} style={{ marginBottom: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '2px' }}>
                  <span>{r.scenario_name}</span>
                  <span>{r.yield_kg_ha.toLocaleString()} kg/ha</span>
                </div>
                <div style={{ height: '20px', background: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${(r.yield_kg_ha / maxYield) * 100}%`,
                    height: '100%',
                    background: '#16a34a',
                  }} />
                </div>
              </div>
            ))}
          </div>

          {/* Table */}
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                <th style={{ padding: '8px', textAlign: 'start' }}>{t('scenario_title')}</th>
                <th style={{ padding: '8px', textAlign: 'end' }}>{t('yield_kg_ha')}</th>
                <th style={{ padding: '8px', textAlign: 'end' }}>{t('revenue_usd_ha')}</th>
                <th style={{ padding: '8px', textAlign: 'end' }}>{t('water_use')}</th>
                <th style={{ padding: '8px', textAlign: 'end' }}>{t('reduction')}</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '8px' }}>{r.scenario_name}</td>
                  <td style={{ padding: '8px', textAlign: 'end' }}>{r.yield_kg_ha.toLocaleString()}</td>
                  <td style={{ padding: '8px', textAlign: 'end' }}>${r.revenue_usd_ha.toLocaleString()}</td>
                  <td style={{ padding: '8px', textAlign: 'end' }}>{r.water_use_mm}</td>
                  <td style={{ padding: '8px', textAlign: 'end', color: r.yield_reduction_pct > 30 ? '#dc2626' : '#16a34a' }}>
                    {r.yield_reduction_pct.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
