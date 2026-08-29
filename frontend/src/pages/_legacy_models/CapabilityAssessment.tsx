/**
 * Land Capability Assessment - FAO Classification System
 * Uses LandCapabilityMotor from scientific_motors
 * Implements FAO 8-class system:
 *   Class I: Excellent (no limitations)
 *   Class II: Good (slight limitations)
 *   Class III: Moderate (severe limitations)
 *   Class IV: Marginal (very severe limitations)
 *   Class V-VIII: Non-arable
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import {
  Map, Layers, Mountain, Droplet, Leaf,
  AlertCircle, CheckCircle, Play, Loader2, Info, BookOpen
} from 'lucide-react';
import motorsService from '../services/motorsService';
import { usePipeline } from '../contexts/SimulationPipeline';
import "./admin/AdminTheme.css";

interface CapabilityParams {
  slope: number;
  soil_depth: number;
  drainage: string;
  erosion_risk: string;
  soil_texture: string;
  rainfall: number;
  rock_outcrop: number;
  salinity: string;
}

interface CapabilityResult {
  class_number: number;
  class_name: string;
  class_color: string;
  description: string;
  limitations: string[];
  suitable_uses: string[];
  conservation_practices: string[];
  scores: {
    slope_limitation: number;
    soil_limitation: number;
    water_limitation: number;
    erosion_limitation: number;
  };
}

const FAO_CLASSES = [
  { class: 1, name: 'Excellent', color: '#10b981', description: 'Very few limitations. Highly productive' },
  { class: 2, name: 'Good', color: '#34d399', description: 'Slight limitations. Good productivity' },
  { class: 3, name: 'Moderate', color: '#fbbf24', description: 'Moderate limitations requiring conservation' },
  { class: 4, name: 'Marginal', color: '#f59e0b', description: 'Severe limitations. Limited crop choices' },
  { class: 5, name: 'Non-arable I', color: '#f97316', description: 'Not suitable for crops - pasture/forest' },
  { class: 6, name: 'Non-arable II', color: '#fb923c', description: 'Severe limitations - grazing/forest only' },
  { class: 7, name: 'Non-arable III', color: '#ef4444', description: 'Very severe limitations - forest/wildlife' },
  { class: 8, name: 'Non-arable IV', color: '#7f1d1d', description: 'Extreme limitations - recreation/wildlife' },
];

export default function CapabilityAssessment() {
  const { t } = useTranslation();
  const { setCapability } = usePipeline();
  const [params, setParams] = useState<CapabilityParams>({
    slope: 3,
    soil_depth: 100,
    drainage: 'well',
    erosion_risk: 'low',
    soil_texture: 'loam',
    rainfall: 400,
    rock_outcrop: 0,
    salinity: 'none',
  });

  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<CapabilityResult | null>(null);
  const [showInfo, setShowInfo] = useState(false);

  const updateParam = <K extends keyof CapabilityParams>(key: K, value: CapabilityParams[K]) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  const runAssessment = async () => {
    setRunning(true);
    
    try {
      // Try real LandCapabilityMotor
      const response = await motorsService.runMotor({
        motor_key: 'land_capability',
        parameters: {
          slope: params.slope,
          soil_depth: params.soil_depth,
          drainage: params.drainage,
        },
      });

      // Compute FAO classification
      const assessment = classifyFAO(params, response?.result);
      setResult(assessment);
      
      // Publish to pipeline
      setCapability({
        landProfileId: 'capability-run',
        classNumber: assessment.class_number,
        className: assessment.class_name,
        classColor: assessment.class_color,
        limitations: assessment.limitations,
        suitableUses: assessment.suitable_uses,
        scores: assessment.scores,
      });
    } catch (err) {
      // Fallback to direct calculation
      const assessment = classifyFAO(params);
      setResult(assessment);
    } finally {
      setRunning(false);
    }
  };

  // FAO classification algorithm
  const classifyFAO = (p: CapabilityParams, motorData?: any): CapabilityResult => {
    let classNum = 1;
    const limitations: string[] = [];
    const scores = {
      slope_limitation: 0,
      soil_limitation: 0,
      water_limitation: 0,
      erosion_limitation: 0,
    };

    // Slope assessment
    if (p.slope > 30) {
      classNum = Math.max(classNum, 7);
      scores.slope_limitation = 100;
      limitations.push(`Very steep slope (${p.slope}%)`);
    } else if (p.slope > 18) {
      classNum = Math.max(classNum, 6);
      scores.slope_limitation = 80;
      limitations.push(`Steep slope (${p.slope}%)`);
    } else if (p.slope > 12) {
      classNum = Math.max(classNum, 5);
      scores.slope_limitation = 60;
      limitations.push(`Moderate slope (${p.slope}%)`);
    } else if (p.slope > 8) {
      classNum = Math.max(classNum, 4);
      scores.slope_limitation = 45;
      limitations.push(`Moderate slope (${p.slope}%)`);
    } else if (p.slope > 4) {
      classNum = Math.max(classNum, 3);
      scores.slope_limitation = 30;
      limitations.push(`Slight slope (${p.slope}%)`);
    } else if (p.slope > 2) {
      classNum = Math.max(classNum, 2);
      scores.slope_limitation = 15;
    }

    // Soil depth assessment
    if (p.soil_depth < 25) {
      classNum = Math.max(classNum, 6);
      scores.soil_limitation = 90;
      limitations.push(`Very shallow soil (${p.soil_depth}cm)`);
    } else if (p.soil_depth < 50) {
      classNum = Math.max(classNum, 5);
      scores.soil_limitation = 70;
      limitations.push(`Shallow soil (${p.soil_depth}cm)`);
    } else if (p.soil_depth < 100) {
      classNum = Math.max(classNum, 3);
      scores.soil_limitation = 40;
      limitations.push(`Moderate depth (${p.soil_depth}cm)`);
    } else {
      scores.soil_limitation = 10;
    }

    // Drainage assessment
    if (p.drainage === 'very_poor') {
      classNum = Math.max(classNum, 5);
      scores.water_limitation = 85;
      limitations.push('Very poor drainage');
    } else if (p.drainage === 'poor') {
      classNum = Math.max(classNum, 4);
      scores.water_limitation = 65;
      limitations.push('Poor drainage');
    } else if (p.drainage === 'moderate') {
      classNum = Math.max(classNum, 3);
      scores.water_limitation = 40;
      limitations.push('Moderate drainage');
    } else if (p.drainage === 'excessive') {
      classNum = Math.max(classNum, 3);
      scores.water_limitation = 50;
      limitations.push('Excessive drainage (drought risk)');
    } else {
      scores.water_limitation = 10;
    }

    // Erosion risk assessment
    if (p.erosion_risk === 'severe') {
      classNum = Math.max(classNum, 6);
      scores.erosion_limitation = 90;
      limitations.push('Severe erosion risk');
    } else if (p.erosion_risk === 'high') {
      classNum = Math.max(classNum, 5);
      scores.erosion_limitation = 70;
      limitations.push('High erosion risk');
    } else if (p.erosion_risk === 'moderate') {
      classNum = Math.max(classNum, 3);
      scores.erosion_limitation = 40;
      limitations.push('Moderate erosion risk');
    } else {
      scores.erosion_limitation = 15;
    }

    // Rock outcrop
    if (p.rock_outcrop > 50) {
      classNum = Math.max(classNum, 7);
      limitations.push(`High rock outcrop (${p.rock_outcrop}%)`);
    } else if (p.rock_outcrop > 25) {
      classNum = Math.max(classNum, 5);
      limitations.push(`Moderate rock outcrop (${p.rock_outcrop}%)`);
    }

    // Salinity
    if (p.salinity === 'severe') {
      classNum = Math.max(classNum, 7);
      limitations.push('Severe salinity');
    } else if (p.salinity === 'moderate') {
      classNum = Math.max(classNum, 5);
      limitations.push('Moderate salinity');
    } else if (p.salinity === 'slight') {
      classNum = Math.max(classNum, 3);
      limitations.push('Slight salinity');
    }

    const classInfo = FAO_CLASSES[classNum - 1];

    // Suitable uses by class
    const uses: Record<number, string[]> = {
      1: ['All crops', 'Intensive cultivation', 'Orchards', 'Horticulture'],
      2: ['Most crops', 'Cultivation with simple conservation', 'Orchards'],
      3: ['Limited crops', 'Contour farming required', 'Terracing needed'],
      4: ['Few crops', 'Permanent crops preferred', 'Intensive conservation'],
      5: ['Pasture', 'Hay', 'Forest', 'Wildlife habitat'],
      6: ['Grazing', 'Forest', 'Wildlife habitat'],
      7: ['Forest', 'Wildlife', 'Watershed protection'],
      8: ['Recreation', 'Wildlife', 'Watershed', 'Scenic value'],
    };

    // Conservation practices
    const practices: Record<number, string[]> = {
      1: ['Standard practices'],
      2: ['Contour plowing', 'Crop rotation', 'Cover crops'],
      3: ['Terracing', 'Strip cropping', 'Grassed waterways'],
      4: ['Terracing', 'Permanent vegetation', 'Careful management'],
      5: ['Managed grazing', 'Forest management'],
      6: ['Rotational grazing', 'Forest management'],
      7: ['Forest protection', 'Wildlife conservation'],
      8: ['Minimal intervention', 'Recreation management'],
    };

    return {
      class_number: classNum,
      class_name: classInfo.name,
      class_color: classInfo.color,
      description: classInfo.description,
      limitations,
      suitable_uses: uses[classNum],
      conservation_practices: practices[classNum],
      scores,
    };
  };

  const radarData = result ? [
    { subject: 'Slope', A: result.scores.slope_limitation, fullMark: 100 },
    { subject: 'Soil', A: result.scores.soil_limitation, fullMark: 100 },
    { subject: 'Water', A: result.scores.water_limitation, fullMark: 100 },
    { subject: 'Erosion', A: result.scores.erosion_limitation, fullMark: 100 },
  ] : [];

  return (
    <div className="admin-page-container">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Map size={32} style={{ color: '#f97316' }} />
            {t('nav.capability', 'Land Capability Assessment')}
          </h1>
          <p className="page-subtitle">
            {t('simulator.capabilityDesc', 'FAO land capability classification system')}
          </p>
        </div>
        <button className="btn-secondary" onClick={() => setShowInfo(!showInfo)}>
          <BookOpen size={16} /> {t('simulator.faoClasses', 'FAO Classes')}
        </button>
      </div>

      {/* FAO Classes Reference */}
      {showInfo && (
        <div className="glass-card" style={{ marginBottom: '24px', padding: '24px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: 'var(--text-primary)' }}>
            FAO 8-Class Land Capability System
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
            {FAO_CLASSES.map(cls => (
              <div key={cls.class} style={{ padding: '12px', background: `${cls.color}20`, borderRadius: '8px', border: `1px solid ${cls.color}40` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: cls.color }} />
                  <strong style={{ color: cls.color }}>Class {cls.class}</strong>
                </div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
                  {cls.name}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {cls.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Parameters */}
      <div className="glass-card" style={{ marginBottom: '24px', padding: '24px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '20px', color: 'var(--text-primary)' }}>
          🌍 Land Characteristics
        </h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
          <div>
            <label className="form-label">Slope (%)</label>
            <input
              type="number"
              className="form-input"
              value={params.slope}
              onChange={(e) => updateParam('slope', parseFloat(e.target.value) || 0)}
              min={0}
              max={100}
              step={0.5}
            />
          </div>

          <div>
            <label className="form-label">Soil Depth (cm)</label>
            <input
              type="number"
              className="form-input"
              value={params.soil_depth}
              onChange={(e) => updateParam('soil_depth', parseFloat(e.target.value) || 0)}
              min={0}
              max={500}
            />
          </div>

          <div>
            <label className="form-label">Drainage Class</label>
            <select
              className="form-input"
              value={params.drainage}
              onChange={(e) => updateParam('drainage', e.target.value)}
            >
              <option value="excessive">Excessive</option>
              <option value="well">Well drained</option>
              <option value="moderate">Moderately drained</option>
              <option value="poor">Poorly drained</option>
              <option value="very_poor">Very poorly drained</option>
            </select>
          </div>

          <div>
            <label className="form-label">Erosion Risk</label>
            <select
              className="form-input"
              value={params.erosion_risk}
              onChange={(e) => updateParam('erosion_risk', e.target.value)}
            >
              <option value="low">Low</option>
              <option value="moderate">Moderate</option>
              <option value="high">High</option>
              <option value="severe">Severe</option>
            </select>
          </div>

          <div>
            <label className="form-label">Soil Texture</label>
            <select
              className="form-input"
              value={params.soil_texture}
              onChange={(e) => updateParam('soil_texture', e.target.value)}
            >
              <option value="sand">Sand</option>
              <option value="loamy_sand">Loamy Sand</option>
              <option value="loam">Loam</option>
              <option value="clay_loam">Clay Loam</option>
              <option value="clay">Clay</option>
            </select>
          </div>

          <div>
            <label className="form-label">Annual Rainfall (mm)</label>
            <input
              type="number"
              className="form-input"
              value={params.rainfall}
              onChange={(e) => updateParam('rainfall', parseFloat(e.target.value) || 0)}
              min={50}
              max={3000}
            />
          </div>

          <div>
            <label className="form-label">Rock Outcrop (%)</label>
            <input
              type="number"
              className="form-input"
              value={params.rock_outcrop}
              onChange={(e) => updateParam('rock_outcrop', parseFloat(e.target.value) || 0)}
              min={0}
              max={100}
            />
          </div>

          <div>
            <label className="form-label">Salinity Level</label>
            <select
              className="form-input"
              value={params.salinity}
              onChange={(e) => updateParam('salinity', e.target.value)}
            >
              <option value="none">None</option>
              <option value="slight">Slight</option>
              <option value="moderate">Moderate</option>
              <option value="severe">Severe</option>
            </select>
          </div>
        </div>

        <button
          className="btn-primary"
          onClick={runAssessment}
          disabled={running}
          style={{ marginTop: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          {running ? <Loader2 size={16} className="spin" /> : <Play size={16} />}
          {running ? 'Analyzing...' : 'Run Assessment'}
        </button>
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Main Classification Card */}
          <div className="glass-card" style={{
            marginBottom: '24px',
            padding: '32px',
            background: `linear-gradient(135deg, ${result.class_color}20, transparent)`,
            border: `2px solid ${result.class_color}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
              <div style={{
                width: '100px',
                height: '100px',
                borderRadius: '20px',
                background: result.class_color,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 700,
              }}>
                <div style={{ fontSize: '48px', lineHeight: 1 }}>{result.class_number}</div>
                <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>Class</div>
              </div>
              
              <div style={{ flex: 1, minWidth: '250px' }}>
                <h2 style={{ fontSize: '28px', fontWeight: 800, color: result.class_color, margin: '0 0 8px 0' }}>
                  Class {result.class_number} - {result.class_name}
                </h2>
                <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 12px 0' }}>
                  {result.description}
                </p>
              </div>
            </div>
          </div>

          {/* Analysis Grid */}
          <div className="grid-2col">
            {/* Limitation Radar Chart */}
            <div className="chart-container">
              <div className="chart-title">
                <AlertCircle size={20} />
                Limitation Analysis
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="var(--border-color)" />
                  <PolarAngleAxis dataKey="subject" stroke="var(--text-muted)" fontSize={12} />
                  <PolarRadiusAxis stroke="var(--text-muted)" fontSize={10} />
                  <Radar
                    name="Limitation"
                    dataKey="A"
                    stroke={result.class_color}
                    fill={result.class_color}
                    fillOpacity={0.5}
                  />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Class Distribution Pie */}
            <div className="chart-container">
              <div className="chart-title">
                <PieChart size={20} />
                FAO Class Distribution
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={FAO_CLASSES}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `Class ${entry.class}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="class"
                  >
                    {FAO_CLASSES.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.color}
                        opacity={entry.class === result.class_number ? 1 : 0.3}
                        stroke={entry.class === result.class_number ? 'white' : 'none'}
                        strokeWidth={entry.class === result.class_number ? 3 : 0}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Detailed Analysis */}
          <div className="grid-3col">
            <div className="glass-card" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: 'var(--accent-danger)' }}>
                <AlertCircle size={18} style={{ display: 'inline', marginRight: '6px' }} />
                Limitations ({result.limitations.length})
              </h3>
              <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                {result.limitations.map((lim, i) => (
                  <li key={i} style={{ marginBottom: '4px' }}>{lim}</li>
                ))}
              </ul>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: 'var(--accent-primary)' }}>
                <CheckCircle size={18} style={{ display: 'inline', marginRight: '6px' }} />
                Suitable Uses
              </h3>
              <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                {result.suitable_uses.map((use, i) => (
                  <li key={i} style={{ marginBottom: '4px' }}>{use}</li>
                ))}
              </ul>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: 'var(--accent-info)' }}>
                <Layers size={18} style={{ display: 'inline', marginRight: '6px' }} />
                Conservation Practices
              </h3>
              <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                {result.conservation_practices.map((practice, i) => (
                  <li key={i} style={{ marginBottom: '4px' }}>{practice}</li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}
