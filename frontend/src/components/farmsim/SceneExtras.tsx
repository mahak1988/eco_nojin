import { useMemo } from 'react';
import { Instances, Instance, Line, Html } from '@react-three/drei';
import * as THREE from 'three';
import type { TerrainData } from '../../lib/terrainGenerator';

// ===== Seeded RNG =====
export function mulberry32(a: number) {
  return function() {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ===== Elevation at world (x,z) =====
export function elevAt(t: TerrainData, x: number, z: number): number {
  const gx = Math.max(0, Math.min(t.width - 1, Math.floor((x + 10) / 20 * t.width)));
  const gz = Math.max(0, Math.min(t.height - 1, Math.floor((z + 10) / 20 * t.height)));
  return t.elevation[gz]?.[gx] ?? t.minElevation;
}

// ===== Scientific data at a point =====
export interface PlotData {
  moisture: number; ndvi: number; erosion: number; slope: number; elevation: number;
}
export function samplePlotData(t: TerrainData, x: number, z: number): PlotData {
  const gx = Math.max(0, Math.min(t.width - 1, Math.floor((x + 10) / 20 * t.width)));
  const gz = Math.max(0, Math.min(t.height - 1, Math.floor((z + 10) / 20 * t.height)));
  const range = t.maxElevation - t.minElevation || 1;
  const elev = t.elevation[gz]?.[gx] ?? t.minElevation;
  const zL = t.elevation[gz]?.[Math.max(0, gx - 1)] ?? elev;
  const zR = t.elevation[gz]?.[Math.min(t.width - 1, gx + 1)] ?? elev;
  const zU = t.elevation[Math.max(0, gz - 1)]?.[gx] ?? elev;
  const zD = t.elevation[Math.min(t.height - 1, gz + 1)]?.[gx] ?? elev;
  const slope = Math.atan(Math.sqrt(((zR - zL) / 2) ** 2 + ((zD - zU) / 2) ** 2) / 20) * 180 / Math.PI;
  return {
    moisture: t.moisture[gz]?.[gx] ?? 0,
    ndvi: Math.max(0, Math.min(1, (t.moisture[gz]?.[gx] ?? 0) * 0.6 + ((elev - t.minElevation) / range) * 0.4)),
    erosion: t.erosion[gz]?.[gx] ?? 0,
    slope,
    elevation: elev,
  };
}

export interface DataPlot {
  id: string; center: [number, number]; size: [number, number]; data: PlotData;
}

// ===== Data plot: green dashed outline + floating label =====
export function DataPlotView({ plot }: { plot: DataPlot }) {
  const [cx, cz] = plot.center;
  const [w, d] = plot.size;
  const y = 0.12;
  const outline: [number, number, number][] = [
    [cx - w / 2, y, cz - d / 2], [cx + w / 2, y, cz - d / 2],
    [cx + w / 2, y, cz + d / 2], [cx - w / 2, y, cz + d / 2],
    [cx - w / 2, y, cz - d / 2],
  ];
  const dta = plot.data;
  return (
    <group>
      <mesh position={[cx, y - 0.02, cz]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[w, d]} />
        <meshStandardMaterial color="#6fae5a" roughness={1} />
      </mesh>
      <Line points={outline} color="#39ff5a" lineWidth={3} dashed dashScale={2} />
      <Html position={[cx, 2.4, cz]} center zIndexRange={[100, 0]} style={{ pointerEvents: 'none' }}>
        <div style={{
          background: 'rgba(10,20,10,0.88)', color: 'white', borderRadius: 10,
          padding: '8px 12px', fontFamily: 'var(--font-persian, Tahoma)', fontSize: 11,
          border: '1px solid rgba(57,255,90,0.5)', boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
          whiteSpace: 'nowrap', backdropFilter: 'blur(6px)',
        }}>
          <div style={{ fontWeight: 800, color: '#39ff5a', marginBottom: 4 }}>📊 داده زمین</div>
          <div>💧 رطوبت: <b>{Math.round(dta.moisture * 100)}%</b></div>
          <div>🌿 NDVI: <b>{dta.ndvi.toFixed(2)}</b></div>
          <div>⛰️ شیب: <b>{dta.slope.toFixed(1)}°</b></div>
          <div>⚠️ فرسایش: <b>{dta.erosion.toFixed(1)}</b></div>
          <div>📐 ارتفاع: <b>{Math.round(dta.elevation)}m</b></div>
        </div>
      </Html>
    </group>
  );
}

// ===== Instanced crops (terrain-aware) =====
export function Crops({ terrain, center, size, growth, color }: {
  terrain: TerrainData; center: [number, number]; size: [number, number];
  growth: number; color: string;
}) {
  const plants = useMemo(() => {
    const rand = mulberry32(99);
    const [w, d] = size; const [cx, cz] = center;
    const pts: [number, number, number][] = [];
    const rows = Math.floor(d / 0.7), cols = Math.floor(w / 0.5);
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const x = cx - w / 2 + 0.3 + c * 0.5 + (rand() - 0.5) * 0.08;
      const z = cz - d / 2 + 0.3 + r * 0.7 + (rand() - 0.5) * 0.08;
      pts.push([x, elevAt(terrain, x, z), z]);
    }
    return pts;
  }, [terrain, center, size]);
  const s = 0.3 + growth * 0.8;
  return (
    <Instances limit={plants.length} castShadow>
      <coneGeometry args={[0.13, 0.7, 5]} />
      <meshStandardMaterial color={color} roughness={0.8} />
      {plants.map((p, i) => (
        <Instance key={i} position={[p[0], p[1] + 0.35 * s, p[2]]} scale={s} />
      ))}
    </Instances>
  );
}

// ===== Instanced trees (terrain-aware) =====
export function Forest({ terrain, count = 90, seed = 5, radius = 24 }: {
  terrain: TerrainData; count?: number; seed?: number; radius?: number;
}) {
  const trees = useMemo(() => {
    const rand = mulberry32(seed);
    const pts: { x: number; z: number; s: number; pine: boolean; y: number }[] = [];
    for (let i = 0; i < count; i++) {
      const a = rand() * Math.PI * 2;
      const r = radius * (0.7 + rand() * 0.6);
      const x = Math.cos(a) * r, z = Math.sin(a) * r;
      pts.push({ x, z, s: 0.7 + rand() * 0.8, pine: rand() > 0.4, y: elevAt(terrain, x, z) });
    }
    return pts;
  }, [terrain, count, seed, radius]);
  const pines = trees.filter(t => t.pine), decid = trees.filter(t => !t.pine);
  return (
    <group>
      <Instances limit={pines.length} castShadow>
        <coneGeometry args={[0.9, 3, 8]} />
        <meshStandardMaterial color="#2d6a2d" />
        {pines.map((t, i) => <Instance key={i} position={[t.x, t.y + 1.6 * t.s, t.z]} scale={t.s} />)}
      </Instances>
      <Instances limit={decid.length} castShadow>
        <sphereGeometry args={[1.1, 10, 10]} />
        <meshStandardMaterial color="#4f8f3f" />
        {decid.map((t, i) => <Instance key={i} position={[t.x, t.y + 1.8 * t.s, t.z]} scale={t.s} />)}
      </Instances>
    </group>
  );
}

// ===== Barn + Silo (terrain-aware) =====
export function Barn({ terrain, position, rotation = 0, scale = 1 }: any) {
  const y = elevAt(terrain, position[0], position[2]);
  return (
    <group position={[position[0], y, position[2]]} rotation={[0, rotation, 0]} scale={scale}>
      <mesh position={[0, 1.2, 0]} castShadow><boxGeometry args={[4, 2.4, 6]} /><meshStandardMaterial color="#7a5a42" roughness={0.9} /></mesh>
      <mesh position={[0, 3, 0]} rotation={[0, Math.PI / 4, 0]} castShadow><coneGeometry args={[3.4, 1.6, 4]} /><meshStandardMaterial color="#2d5a3d" roughness={0.7} /></mesh>
      <mesh position={[0, 0.9, 3.02]}><boxGeometry args={[1.4, 1.8, 0.1]} /><meshStandardMaterial color="#4a3526" /></mesh>
    </group>
  );
}
export function Silo({ terrain, position, scale = 1 }: any) {
  const y = elevAt(terrain, position[0], position[2]);
  return (
    <group position={[position[0], y, position[2]]} scale={scale}>
      <mesh position={[0, 2.2, 0]} castShadow><cylinderGeometry args={[1.1, 1.1, 4.4, 20]} /><meshStandardMaterial color="#9aa0a8" metalness={0.7} roughness={0.3} /></mesh>
      <mesh position={[0, 4.6, 0]} castShadow><coneGeometry args={[1.1, 0.9, 20]} /><meshStandardMaterial color="#7a8088" metalness={0.7} roughness={0.3} /></mesh>
    </group>
  );
}
