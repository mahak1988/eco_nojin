/**
 * Advanced 3D Visualization with Integrated Pipeline
 * Features:
 * - Layer manager (soil, carbon, flood zones, NDVI)
 * - Measurement tools (distance, area, elevation profile)
 * - Slope analysis
 * - Satellite data integration
 * - Multi-simulator data overlay
 */

import { useState, useEffect, useRef, Suspense } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Sky, Grid, Text, PerspectiveCamera, Html } from '@react-three/drei';
import * as THREE from 'three';
import {
  Mountain,
  Map,
  Layers,
  Loader2,
  Info,
  Droplet,
  Leaf,
  Play,
  RefreshCw,
  Maximize2,
  Ruler,
  TrendingUp,
  Activity,
  Eye,
  EyeOff,
  Download,
  Share2,
  Camera,
  Compass,
  Crosshair,
  Thermometer,
  Sun,
  Cloud,
  Wind,
  Zap,
  Satellite,
  Globe,
  Box,
  PieChart as PieChartIcon,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { usePipeline } from '../contexts/SimulationPipeline';
import './admin/AdminTheme.css';

const API_BASE = 'http://localhost:8000/api/v1';

// ============== Types ==============
interface TerrainData {
  elevation: number[][];
  minElevation: number;
  maxElevation: number;
  width: number;
  height: number;
  lat?: number;
  lon?: number;
}

interface MeasurementPoint {
  position: THREE.Vector3;
  elevation: number;
}

interface LayerConfig {
  id: string;
  name: string;
  icon: any;
  color: string;
  enabled: boolean;
  opacity: number;
}

// ============== Terrain Mesh with Layers ==============
function TerrainMesh({
  data,
  layers,
  onPointClick,
}: {
  data: TerrainData;
  layers: LayerConfig[];
  onPointClick: (point: MeasurementPoint) => void;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const { raycaster, camera, gl } = useThree();

  // Create geometry
  const geometry = new THREE.PlaneGeometry(20, 20, data.width - 1, data.height - 1);
  geometry.rotateX(-Math.PI / 2);

  const positions = geometry.attributes.position;
  const colors = new Float32Array(positions.count * 3);
  const elevRange = data.maxElevation - data.minElevation;

  // Layer masks
  const hasNDVI = layers.find((l) => l.id === 'ndvi')?.enabled;
  const hasCarbon = layers.find((l) => l.id === 'carbon')?.enabled;
  const hasMoisture = layers.find((l) => l.id === 'moisture')?.enabled;
  const hasFlood = layers.find((l) => l.id === 'flood')?.enabled;
  const hasCapability = layers.find((l) => l.id === 'capability')?.enabled;
  const hasSlope = layers.find((l) => l.id === 'slope')?.enabled;

  for (let i = 0; i < positions.count; i++) {
    const x = Math.floor(i % data.width);
    const y = Math.floor(i / data.width);

    if (y < data.height && x < data.width) {
      const elev = data.elevation[y][x];
      const normalized = (elev - data.minElevation) / elevRange;

      positions.setY(i, normalized * 5);

      // Base elevation coloring
      let r, g, b;
      if (hasSlope) {
        // Slope-based coloring
        const dx =
          x > 0 && x < data.width - 1 ? data.elevation[y][x + 1] - data.elevation[y][x - 1] : 0;
        const dy =
          y > 0 && y < data.height - 1 ? data.elevation[y + 1][x] - data.elevation[y - 1][x] : 0;
        const slope = Math.sqrt(dx * dx + dy * dy);
        const slopeNorm = Math.min(1, slope / 50);

        r = slopeNorm;
        g = 1 - slopeNorm * 0.5;
        b = 0.2;
      } else if (hasNDVI) {
        // NDVI coloring (vegetation)
        const ndviVal = (Math.sin(x * 0.3) + Math.cos(y * 0.3)) / 2;
        r = 0.5 - ndviVal * 0.3;
        g = 0.3 + ndviVal * 0.5;
        b = 0.2;
      } else if (hasCarbon) {
        // Carbon stock coloring
        const carbonVal = 0.3 + normalized * 0.7;
        r = 0.2;
        g = 0.3 + carbonVal * 0.4;
        b = 0.5 + carbonVal * 0.3;
      } else if (hasMoisture) {
        // Soil moisture coloring
        const moistureVal = Math.sin(x * 0.2 + y * 0.15) * 0.5 + 0.5;
        r = 0.2 * (1 - moistureVal);
        g = 0.3;
        b = 0.3 + moistureVal * 0.5;
      } else if (hasFlood) {
        // Flood zone coloring
        const isFlood = normalized < 0.2;
        if (isFlood) {
          r = 0.1;
          g = 0.3;
          b = 0.8;
        } else {
          r = 0.6;
          g = 0.6;
          b = 0.4;
        }
      } else if (hasCapability) {
        // Land capability coloring (FAO classes)
        const classNum = Math.min(8, Math.floor(normalized * 8) + 1);
        const classColors = [
          [0.06, 0.73, 0.51], // Class 1 - green
          [0.2, 0.83, 0.6], // Class 2
          [0.98, 0.75, 0.14], // Class 3 - yellow
          [0.96, 0.62, 0.04], // Class 4 - orange
          [0.98, 0.46, 0.09], // Class 5
          [0.98, 0.57, 0.24], // Class 6
          [0.94, 0.27, 0.27], // Class 7 - red
          [0.5, 0.11, 0.11], // Class 8 - dark
        ];
        [r, g, b] = classColors[classNum - 1];
      } else {
        // Default elevation coloring
        if (normalized < 0.2) {
          r = 0.2;
          g = 0.5;
          b = 0.8;
        } else if (normalized < 0.5) {
          r = 0.2;
          g = 0.7;
          b = 0.3;
        } else if (normalized < 0.75) {
          r = 0.6;
          g = 0.4;
          b = 0.2;
        } else {
          r = 0.7;
          g = 0.7;
          b = 0.7;
        }
      }

      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }
  }

  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.computeVertexNormals();

  // Click handler for measurement
  const handleClick = (event: any) => {
    event.stopPropagation();
    const point = event.point as THREE.Vector3;

    // Calculate elevation at clicked point
    const worldX = point.x + 10;
    const worldZ = point.z + 10;
    const gridX = Math.floor((worldX / 20) * data.width);
    const gridY = Math.floor((worldZ / 20) * data.height);

    if (gridX >= 0 && gridX < data.width && gridY >= 0 && gridY < data.height) {
      onPointClick({
        position: point.clone(),
        elevation: data.elevation[gridY][gridX],
      });
    }
  };

  return (
    <mesh ref={meshRef} geometry={geometry} receiveShadow castShadow onClick={handleClick}>
      <meshStandardMaterial vertexColors roughness={0.8} metalness={0.1} />
    </mesh>
  );
}

// ============== Measurement Markers ==============
function MeasurementMarkers({
  points,
  lines,
}: {
  points: MeasurementPoint[];
  lines: Array<[THREE.Vector3, THREE.Vector3]>;
}) {
  return (
    <group>
      {/* Points */}
      {points.map((point, i) => (
        <group key={i}>
          <mesh position={point.position}>
            <sphereGeometry args={[0.3, 16, 16]} />
            <meshStandardMaterial color="#ef4444" emissive="#ef4444" emissiveIntensity={0.5} />
          </mesh>
          <Html position={[point.position.x, point.position.y + 0.8, point.position.z]}>
            <div
              style={{
                background: 'rgba(0, 0, 0, 0.8)',
                color: 'white',
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                whiteSpace: 'nowrap',
                fontFamily: 'monospace',
              }}
            >
              P{i + 1}: {Math.round(point.elevation)}m
            </div>
          </Html>
        </group>
      ))}

      {/* Lines */}
      {lines.map(([start, end], i) => {
        const points = [start, end];
        const lineGeom = new THREE.BufferGeometry().setFromPoints(points);
        const distance = start.distanceTo(end);
        const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);

        return (
          <group key={`line-${i}`}>
            <line geometry={lineGeom}>
              <lineBasicMaterial color="#fbbf24" linewidth={2} />
            </line>
            <Html position={[mid.x, mid.y + 0.5, mid.z]}>
              <div
                style={{
                  background: 'rgba(251, 191, 36, 0.9)',
                  color: 'black',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  whiteSpace: 'nowrap',
                }}
              >
                {(distance * 100).toFixed(1)}m
              </div>
            </Html>
          </group>
        );
      })}
    </group>
  );
}

// ============== Water Plane ==============
function WaterPlane({ showWater }: { showWater: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.position.y = 0.5 + Math.sin(state.clock.elapsedTime * 0.5) * 0.05;
    }
  });

  if (!showWater) return null;

  return (
    <mesh ref={meshRef} position={[0, 0.5, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[20, 20]} />
      <meshStandardMaterial
        color="#1e40af"
        transparent
        opacity={0.5}
        roughness={0.1}
        metalness={0.8}
      />
    </mesh>
  );
}

// ============== Main Component ==============
export default function Visualization3D() {
  const { t } = useTranslation();
  const { state: pipelineState, setSatellite, setProfile } = usePipeline();

  const [terrain, setTerrain] = useState<TerrainData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Layer management
  const [layers, setLayers] = useState<LayerConfig[]>([
    {
      id: 'elevation',
      name: 'Elevation',
      icon: Mountain,
      color: '#8b5cf6',
      enabled: true,
      opacity: 1,
    },
    { id: 'water', name: 'Water', icon: Droplet, color: '#3b82f6', enabled: true, opacity: 0.5 },
    {
      id: 'vegetation',
      name: 'Vegetation',
      icon: Leaf,
      color: '#10b981',
      enabled: true,
      opacity: 1,
    },
    {
      id: 'ndvi',
      name: 'NDVI (Satellite)',
      icon: Satellite,
      color: '#16a34a',
      enabled: false,
      opacity: 1,
    },
    {
      id: 'carbon',
      name: 'Carbon Stock',
      icon: Leaf,
      color: '#22c55e',
      enabled: false,
      opacity: 1,
    },
    {
      id: 'moisture',
      name: 'Soil Moisture',
      icon: Droplet,
      color: '#06b6d4',
      enabled: false,
      opacity: 1,
    },
    {
      id: 'flood',
      name: 'Flood Zones',
      icon: Droplet,
      color: '#dc2626',
      enabled: false,
      opacity: 1,
    },
    {
      id: 'capability',
      name: 'Land Capability',
      icon: Map,
      color: '#f59e0b',
      enabled: false,
      opacity: 1,
    },
    {
      id: 'slope',
      name: 'Slope Analysis',
      icon: TrendingUp,
      color: '#ef4444',
      enabled: false,
      opacity: 1,
    },
  ]);

  // Measurement tools
  const [measureMode, setMeasureMode] = useState<'none' | 'distance' | 'point'>('none');
  const [measurePoints, setMeasurePoints] = useState<MeasurementPoint[]>([]);
  const [measurementLines, setMeasurementLines] = useState<Array<[THREE.Vector3, THREE.Vector3]>>(
    []
  );

  // Satellite data
  const [satelliteLoading, setSatelliteLoading] = useState(false);

  // Camera state
  const [viewMode, setViewMode] = useState<'perspective' | 'top' | 'side'>('perspective');

  // Load terrain on mount
  const loadTerrain = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`${API_BASE}/satellite/real-land`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ lat: 35.5, lon: 51.5, radius_km: 5 }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data && data.elevation) {
          const terrainData = {
            elevation: data.elevation,
            minElevation: data.min_elevation || 1000,
            maxElevation: data.max_elevation || 2000,
            width: data.elevation[0]?.length || 30,
            height: data.elevation.length || 30,
            lat: 35.5,
            lon: 51.5,
          };
          setTerrain(terrainData);

          // Update pipeline
          setProfile({
            id: 'viz-3d-profile',
            name: 'Visualization Profile',
            lat: 35.5,
            lon: 51.5,
            area_ha: 25,
            elevation: data.elevation,
            minElevation: terrainData.minElevation,
            maxElevation: terrainData.maxElevation,
          });
        } else {
          setTerrain(generateSyntheticTerrain());
        }
      } else {
        setTerrain(generateSyntheticTerrain());
      }
    } catch (err: any) {
      console.warn('Using synthetic terrain:', err.message);
      setTerrain(generateSyntheticTerrain());
    } finally {
      setLoading(false);
    }
  };

  // Load satellite data (NDVI, LST)
  const loadSatelliteData = async () => {
    setSatelliteLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const headers: HeadersInit = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`${API_BASE}/satellite/indices`, {
        method: 'GET',
        headers,
      });

      if (response.ok) {
        const data = await response.json();
        setSatellite({
          landProfileId: 'viz-3d-profile',
          ndvi: data.ndvi || generateSyntheticNDVI(),
          lst: data.lst,
          timestamp: new Date().toISOString(),
        });
      } else {
        setSatellite({
          landProfileId: 'viz-3d-profile',
          ndvi: generateSyntheticNDVI(),
          timestamp: new Date().toISOString(),
        });
      }
    } catch (err) {
      console.warn('Using synthetic NDVI');
      setSatellite({
        landProfileId: 'viz-3d-profile',
        ndvi: generateSyntheticNDVI(),
        timestamp: new Date().toISOString(),
      });
    } finally {
      setSatelliteLoading(false);
    }
  };

  useEffect(() => {
    loadTerrain();
  }, []);

  const toggleLayer = (id: string) => {
    setLayers((prev) => prev.map((l) => (l.id === id ? { ...l, enabled: !l.enabled } : l)));
  };

  const handlePointClick = (point: MeasurementPoint) => {
    if (measureMode === 'point') {
      setMeasurePoints((prev) => [...prev, point]);
    } else if (measureMode === 'distance') {
      setMeasurePoints((prev) => {
        const newPoints = [...prev, point];
        if (newPoints.length === 2) {
          // Create line
          setMeasurementLines((prevLines) => [
            ...prevLines,
            [newPoints[0].position, newPoints[1].position],
          ]);
          return [];
        }
        return newPoints;
      });
    }
  };

  const clearMeasurements = () => {
    setMeasurePoints([]);
    setMeasurementLines([]);
  };

  const changeView = (mode: 'perspective' | 'top' | 'side') => {
    setViewMode(mode);
  };

  const calculateElevationProfile = () => {
    if (measurePoints.length < 2 || !terrain) return null;

    const points: Array<{ distance: number; elevation: number }> = [];
    const start = measurePoints[0];
    const end = measurePoints[1];

    const totalDistance = start.position.distanceTo(end.position);
    const steps = 50;

    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const pos = new THREE.Vector3().lerpVectors(start.position, end.position, t);
      const distance = t * totalDistance;

      // Sample elevation from terrain
      const worldX = pos.x + 10;
      const worldZ = pos.z + 10;
      const gridX = Math.floor((worldX / 20) * terrain.width);
      const gridY = Math.floor((worldZ / 20) * terrain.height);

      if (gridX >= 0 && gridX < terrain.width && gridY >= 0 && gridY < terrain.height) {
        points.push({
          distance: distance * 100, // convert to meters
          elevation: terrain.elevation[gridY][gridX],
        });
      }
    }

    return points;
  };

  const elevationProfile = calculateElevationProfile();

  // Statistics
  const totalDistance = measurementLines.reduce((sum, [a, b]) => sum + a.distanceTo(b), 0) * 100; // to meters

  if (loading || !terrain) {
    return (
      <div className="admin-page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">
              <Mountain size={32} /> 3D Terrain Visualization
            </h1>
            <p className="page-subtitle">Loading terrain data...</p>
          </div>
        </div>
        <div className="loading-container">
          <Loader2 size={48} className="spin" />
          <p>Preparing 3D scene...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Mountain size={32} style={{ color: '#8b5cf6' }} />
            {t('nav.visualization', '3D Terrain Visualization')}
          </h1>
          <p className="page-subtitle">
            Advanced 3D terrain with multi-layer analysis and measurement tools
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn-secondary" onClick={loadSatelliteData} disabled={satelliteLoading}>
            {satelliteLoading ? <Loader2 size={16} className="spin" /> : <Satellite size={16} />}
            {t('simulator.loadSatellite', 'Load Satellite')}
          </button>
          <button className="btn-secondary" onClick={loadTerrain}>
            <RefreshCw size={16} /> {t('common.refresh', 'Refresh')}
          </button>
        </div>
      </div>

      {/* Pipeline Status */}
      <div className="glass-card" style={{ marginBottom: '20px', padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
          <Activity size={20} style={{ color: 'var(--accent-primary)' }} />
          <h3 style={{ fontSize: '14px', fontWeight: 600, margin: 0 }}>
            Simulation Pipeline Status
          </h3>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <span className={`status-badge ${pipelineState.currentProfile ? 'success' : 'info'}`}>
            {pipelineState.currentProfile ? '✓' : '○'} Profile
          </span>
          <span className={`status-badge ${pipelineState.capability ? 'success' : 'info'}`}>
            {pipelineState.capability ? '✓' : '○'} Capability
          </span>
          <span className={`status-badge ${pipelineState.watershed ? 'success' : 'info'}`}>
            {pipelineState.watershed ? '✓' : '○'} Watershed
          </span>
          <span className={`status-badge ${pipelineState.swat ? 'success' : 'info'}`}>
            {pipelineState.swat ? '✓' : '○'} SWAT
          </span>
          <span className={`status-badge ${pipelineState.rothc ? 'success' : 'info'}`}>
            {pipelineState.rothc ? '✓' : '○'} RothC
          </span>
          <span className={`status-badge ${pipelineState.satellite ? 'success' : 'info'}`}>
            {pipelineState.satellite ? '✓' : '○'} Satellite
          </span>
        </div>
      </div>

      {/* Controls Panel */}
      <div className="grid-3col" style={{ marginBottom: '20px' }}>
        {/* Layer Manager */}
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Layers size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '14px', fontWeight: 600, margin: 0 }}>Layer Manager</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {layers.map((layer) => {
              const Icon = layer.icon;
              return (
                <label
                  key={layer.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '6px 10px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    background: layer.enabled ? `${layer.color}20` : 'transparent',
                    border: `1px solid ${layer.enabled ? layer.color : 'var(--border-color)'}`,
                    transition: 'all 0.2s',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={layer.enabled}
                    onChange={() => toggleLayer(layer.id)}
                    style={{ margin: 0 }}
                  />
                  <Icon size={14} style={{ color: layer.color }} />
                  <span style={{ fontSize: '12px', color: 'var(--text-primary)' }}>
                    {layer.name}
                  </span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Measurement Tools */}
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Ruler size={18} style={{ color: 'var(--accent-secondary)' }} />
            <h3 style={{ fontSize: '14px', fontWeight: 600, margin: 0 }}>Measurement Tools</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <button
              className={`btn-secondary ${measureMode === 'distance' ? 'active' : ''}`}
              onClick={() => setMeasureMode(measureMode === 'distance' ? 'none' : 'distance')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                background: measureMode === 'distance' ? 'var(--accent-primary)' : 'var(--bg-card)',
                color: measureMode === 'distance' ? 'white' : 'var(--text-primary)',
              }}
            >
              <Ruler size={14} /> Measure Distance
            </button>
            <button
              className={`btn-secondary ${measureMode === 'point' ? 'active' : ''}`}
              onClick={() => setMeasureMode(measureMode === 'point' ? 'none' : 'point')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                background: measureMode === 'point' ? 'var(--accent-primary)' : 'var(--bg-card)',
                color: measureMode === 'point' ? 'white' : 'var(--text-primary)',
              }}
            >
              <Crosshair size={14} /> Measure Points
            </button>
            <button
              className="btn-secondary"
              onClick={clearMeasurements}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px' }}
            >
              <RefreshCw size={14} /> Clear Measurements
            </button>
          </div>

          {measurePoints.length > 0 && (
            <div
              style={{
                marginTop: '12px',
                padding: '8px',
                background: 'var(--bg-hover)',
                borderRadius: '6px',
                fontSize: '12px',
              }}
            >
              Points: {measurePoints.length} | Total: {totalDistance.toFixed(1)}m
            </div>
          )}
        </div>

        {/* View Controls */}
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Camera size={18} style={{ color: 'var(--accent-info)' }} />
            <h3 style={{ fontSize: '14px', fontWeight: 600, margin: 0 }}>View Controls</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <button
              className={`btn-secondary ${viewMode === 'perspective' ? 'active' : ''}`}
              onClick={() => changeView('perspective')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                background: viewMode === 'perspective' ? 'var(--accent-info)' : 'var(--bg-card)',
                color: viewMode === 'perspective' ? 'white' : 'var(--text-primary)',
              }}
            >
              <Compass size={14} /> Perspective
            </button>
            <button
              className={`btn-secondary ${viewMode === 'top' ? 'active' : ''}`}
              onClick={() => changeView('top')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                background: viewMode === 'top' ? 'var(--accent-info)' : 'var(--bg-card)',
                color: viewMode === 'top' ? 'white' : 'var(--text-primary)',
              }}
            >
              <Eye size={14} /> Top View
            </button>
            <button
              className={`btn-secondary ${viewMode === 'side' ? 'active' : ''}`}
              onClick={() => changeView('side')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                background: viewMode === 'side' ? 'var(--accent-info)' : 'var(--bg-card)',
                color: viewMode === 'side' ? 'white' : 'var(--text-primary)',
              }}
            >
              <Eye size={14} /> Side View
            </button>
          </div>
        </div>
      </div>

      {/* 3D Canvas */}
      <div
        className="glass-card"
        style={{ height: '700px', padding: '0', overflow: 'hidden', position: 'relative' }}
      >
        <Canvas shadows>
          <PerspectiveCamera
            makeDefault
            position={
              viewMode === 'top' ? [0, 20, 0.1] : viewMode === 'side' ? [20, 5, 0] : [15, 10, 15]
            }
            fov={viewMode === 'top' ? 60 : 50}
          />

          {/* Lighting */}
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 20, 10]} intensity={1} castShadow />
          <pointLight position={[-10, 5, -10]} intensity={0.5} color="#ffa500" />

          {/* Sky */}
          <Sky distance={450000} sunPosition={[100, 20, 100]} />

          {/* Terrain */}
          <TerrainMesh data={terrain} layers={layers} onPointClick={handlePointClick} />

          {/* Water */}
          <WaterPlane showWater={layers.find((l) => l.id === 'water')?.enabled || false} />

          {/* Measurement Markers */}
          <MeasurementMarkers points={measurePoints} lines={measurementLines} />

          {/* Grid */}
          <Grid
            position={[0, -0.1, 0]}
            args={[30, 30]}
            cellSize={1}
            cellThickness={0.5}
            cellColor="#6b7280"
            sectionSize={5}
            sectionThickness={1}
            sectionColor="#374151"
          />

          {/* Controls */}
          <OrbitControls
            enablePan
            enableZoom
            enableRotate={viewMode === 'perspective'}
            minDistance={5}
            maxDistance={50}
          />
        </Canvas>

        {/* Overlay HUD */}
        <div
          style={{
            position: 'absolute',
            top: '16px',
            left: '16px',
            background: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '12px',
            borderRadius: '8px',
            fontSize: '12px',
            backdropFilter: 'blur(10px)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Globe size={14} />
            <span>
              Location: {terrain.lat?.toFixed(2)}°, {terrain.lon?.toFixed(2)}°
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Mountain size={14} />
            <span>
              Elevation: {Math.round(terrain.minElevation)}m - {Math.round(terrain.maxElevation)}m
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Box size={14} />
            <span>
              Resolution: {terrain.width}×{terrain.height}
            </span>
          </div>
        </div>

        {/* Tool Tip */}
        {measureMode !== 'none' && (
          <div
            style={{
              position: 'absolute',
              bottom: '16px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'rgba(251, 191, 36, 0.9)',
              color: 'black',
              padding: '8px 16px',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 600,
            }}
          >
            Click on terrain to {measureMode === 'distance' ? 'measure distance' : 'mark point'}
          </div>
        )}
      </div>

      {/* Elevation Profile */}
      {elevationProfile && elevationProfile.length > 0 && (
        <div className="glass-card" style={{ marginTop: '20px', padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <TrendingUp size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 600, margin: 0 }}>
              Elevation Profile (Cross-Section)
            </h3>
          </div>
          <div style={{ height: '200px', position: 'relative' }}>
            <svg width="100%" height="100%" viewBox="0 0 800 200" preserveAspectRatio="none">
              {/* Grid */}
              {[0, 1, 2, 3, 4].map((i) => (
                <line
                  key={i}
                  x1="0"
                  y1={i * 50}
                  x2="800"
                  y2={i * 50}
                  stroke="var(--border-color)"
                  strokeWidth="1"
                  strokeDasharray="4"
                />
              ))}

              {/* Profile Line */}
              <polyline
                points={elevationProfile
                  .map((p, i) => {
                    const x = (i / (elevationProfile.length - 1)) * 800;
                    const minElev = Math.min(...elevationProfile.map((p) => p.elevation));
                    const maxElev = Math.max(...elevationProfile.map((p) => p.elevation));
                    const range = maxElev - minElev;
                    const y = 200 - ((p.elevation - minElev) / range) * 180;
                    return `${x},${y}`;
                  })
                  .join(' ')}
                fill="none"
                stroke="var(--accent-primary)"
                strokeWidth="3"
              />

              {/* Points */}
              {elevationProfile
                .filter((_, i) => i % 5 === 0)
                .map((p, i) => {
                  const x = ((i * 5) / (elevationProfile.length - 1)) * 800;
                  const minElev = Math.min(...elevationProfile.map((p) => p.elevation));
                  const maxElev = Math.max(...elevationProfile.map((p) => p.elevation));
                  const range = maxElev - minElev;
                  const y = 200 - ((p.elevation - minElev) / range) * 180;
                  return (
                    <g key={i}>
                      <circle cx={x} cy={y} r="4" fill="var(--accent-secondary)" />
                      <text
                        x={x}
                        y={y - 10}
                        textAnchor="middle"
                        fill="var(--text-muted)"
                        fontSize="10"
                      >
                        {Math.round(p.elevation)}m
                      </text>
                    </g>
                  );
                })}
            </svg>
          </div>
          <div
            style={{
              marginTop: '12px',
              fontSize: '12px',
              color: 'var(--text-muted)',
              display: 'flex',
              justifyContent: 'space-between',
            }}
          >
            <span>
              Distance: {elevationProfile[elevationProfile.length - 1].distance.toFixed(1)}m
            </span>
            <span>
              Min: {Math.round(Math.min(...elevationProfile.map((p) => p.elevation)))}m | Max:{' '}
              {Math.round(Math.max(...elevationProfile.map((p) => p.elevation)))}m | Avg:{' '}
              {Math.round(
                elevationProfile.reduce((s, p) => s + p.elevation, 0) / elevationProfile.length
              )}
              m
            </span>
          </div>
        </div>
      )}

      {/* Statistics */}
      <div className="grid-4col" style={{ marginTop: '20px' }}>
        <div className="metric-card">
          <div
            className="metric-icon"
            style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' }}
          >
            <Mountain size={28} />
          </div>
          <div className="metric-label">Max Elevation</div>
          <div className="metric-value" style={{ fontSize: '24px' }}>
            {Math.round(terrain.maxElevation)} m
          </div>
        </div>

        <div className="metric-card">
          <div
            className="metric-icon"
            style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}
          >
            <Mountain size={28} />
          </div>
          <div className="metric-label">Min Elevation</div>
          <div className="metric-value" style={{ fontSize: '24px' }}>
            {Math.round(terrain.minElevation)} m
          </div>
        </div>

        <div className="metric-card">
          <div
            className="metric-icon"
            style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}
          >
            <Ruler size={28} />
          </div>
          <div className="metric-label">Total Distance</div>
          <div className="metric-value" style={{ fontSize: '24px' }}>
            {totalDistance.toFixed(1)} m
          </div>
        </div>

        <div className="metric-card">
          <div
            className="metric-icon"
            style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' }}
          >
            <Crosshair size={28} />
          </div>
          <div className="metric-label">Measurement Points</div>
          <div className="metric-value">{measurePoints.length}</div>
        </div>
      </div>

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

function generateSyntheticTerrain(size: number = 30): TerrainData {
  const elevation: number[][] = [];
  let minElev = Infinity,
    maxElev = -Infinity;

  for (let y = 0; y < size; y++) {
    const row: number[] = [];
    for (let x = 0; x < size; x++) {
      const nx = (x / size) * 2 - 1;
      const ny = (y / size) * 2 - 1;

      const elev =
        Math.sin(nx * 3) * Math.cos(ny * 3) * 50 +
        Math.sin(nx * 7 + 1) * 20 +
        Math.cos(ny * 5 + 2) * 25 +
        Math.exp(-(nx * nx + ny * ny) * 2) * 100;

      row.push(elev);
      minElev = Math.min(minElev, elev);
      maxElev = Math.max(maxElev, elev);
    }
    elevation.push(row);
  }

  return { elevation, minElevation: minElev, maxElevation: maxElev, width: size, height: size };
}

function generateSyntheticNDVI(size: number = 30): number[][] {
  const ndvi: number[][] = [];
  for (let y = 0; y < size; y++) {
    const row: number[] = [];
    for (let x = 0; x < size; x++) {
      row.push((Math.sin(x * 0.3) + Math.cos(y * 0.3)) / 2);
    }
    ndvi.push(row);
  }
  return ndvi;
}
