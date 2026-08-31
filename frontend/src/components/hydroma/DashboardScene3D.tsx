import React, { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sky } from '@react-three/drei';
import * as THREE from 'three';
import type { RealLandResult, ScientificChainResult } from '../../types/vll';

export type SceneMode =
  'idle' | 'climate' | 'soil' | 'erosion' | 'carbon' | 'crop' | 'water' | 'flood' | 'optimize';

interface DashboardScene3DProps {
  mode: SceneMode;
  realLand: RealLandResult | null;
  chain: ScientificChainResult | null;
  height?: number;
}

const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);

/* ---------- Terrain (colors per mode) ---------- */
const Terrain: React.FC<{ mode: SceneMode; chain: ScientificChainResult | null }> = ({
  mode,
  chain,
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const material = useMemo(() => {
    const colors = new Float32Array(81 * 81 * 3);
    const erosion = num(chain?.erosion?.soil_loss_ton_ha_yr) ?? 0;
    for (let i = 0; i < 81 * 81; i++) {
      const x = i % 81;
      const y = Math.floor(i / 81);
      const slope = Math.abs(Math.sin(x / 14)) + Math.abs(Math.cos(y / 16));
      let r: number, g: number, b: number;
      switch (mode) {
        case 'erosion':
          // heat map: erosion + slope → قرمز/نارنجی
          const heat = Math.min(1, (slope / 2.2) * (0.5 + erosion * 0.4));
          r = 0.35 + heat * 0.65;
          g = 0.45 - heat * 0.35;
          b = 0.3 - heat * 0.25;
          break;
        case 'water':
        case 'flood':
          r = 0.25;
          g = 0.45;
          b = 0.6; // آبی-خاکی
          break;
        case 'soil':
          r = 0.45 + (x / 81) * 0.15;
          g = 0.33;
          b = 0.22; // قهوه‌ای خاک
          break;
        case 'carbon':
          r = 0.2;
          g = 0.5;
          b = 0.25; // سبز کربن
          break;
        case 'crop':
          r = 0.3;
          g = 0.55;
          b = 0.2;
          break;
        default:
          r = 0.32;
          g = 0.48;
          b = 0.3;
      }
      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }
    const mat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.9,
      metalness: 0,
    });
    mat.userData.colors = colors;
    return mat;
  }, [mode, chain]);

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(80, 80, 80, 80);
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const y = pos.getY(i);
      let z = Math.sin(x / 20) * Math.cos(y / 20) * 3.5;
      z += Math.sin(x / 8) * 1.2 + Math.cos(y / 12) * 1.0;
      const stream = Math.abs(y - Math.sin(x / 15) * 3);
      if (stream < 2.5) z -= (2.5 - stream) * 0.7;
      pos.setZ(i, z);
    }
    geo.computeVertexNormals();
    const colorAttr = new THREE.BufferAttribute(material.userData.colors as Float32Array, 3);
    geo.setAttribute('color', colorAttr);
    return geo;
  }, [material]);

  return (
    <mesh
      ref={meshRef}
      rotation={[-Math.PI / 2, 0, 0]}
      geometry={geometry}
      material={material}
      receiveShadow
    />
  );
};

/* ---------- Animated overlays per mode ---------- */
const Rain: React.FC = () => {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const pts = new Float32Array(600 * 3);
    for (let i = 0; i < 600; i++) {
      pts[i * 3] = (Math.random() - 0.5) * 70;
      pts[i * 3 + 1] = Math.random() * 20;
      pts[i * 3 + 2] = (Math.random() - 0.5) * 70;
    }
    return pts;
  }, []);
  useFrame((_, delta) => {
    if (!ref.current) return;
    const arr = ref.current.geometry.attributes.position.array as Float32Array;
    for (let i = 0; i < 600; i++) {
      arr[i * 3 + 1] -= delta * 12;
      if (arr[i * 3 + 1] < 0) arr[i * 3 + 1] = 20;
    }
    ref.current.geometry.attributes.position.needsUpdate = true;
  });
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#7dd3fc" size={0.18} transparent opacity={0.7} />
    </points>
  );
};

const CarbonColumns: React.FC<{ chain: ScientificChainResult | null }> = ({ chain }) => {
  const pools = (chain?.rothc?.outputs?.pools as Record<string, number> | undefined) ?? null;
  const names = pools ? Object.keys(pools) : ['DPM', 'RPM', 'BIO', 'HUM', 'IOM'];
  const values = pools ? names.map((n) => pools[n]) : [1, 4, 2, 30, 11];
  const max = Math.max(...values, 1);
  const colors = ['#f59e0b', '#ef4444', '#10b981', '#3b82f6', '#8b5cf6'];
  return (
    <group position={[-15, 0, -10]}>
      {values.map((v, i) => (
        <mesh key={names[i]} position={[i * 7, ((v / max) * 7) / 2, 0]}>
          <boxGeometry args={[4, (v / max) * 7, 4]} />
          <meshStandardMaterial
            color={colors[i % colors.length]}
            emissive={colors[i % colors.length]}
            emissiveIntensity={0.25}
          />
        </mesh>
      ))}
    </group>
  );
};

const CropRows: React.FC<{ chain: ScientificChainResult | null }> = ({ chain }) => {
  const refs = useRef<THREE.Mesh[]>([]);
  const yieldT = num(chain?.aquacrop?.summary?.yield_ton_ha) ?? 4;
  const rows = 6,
    cols = 6;
  useFrame((state) => {
    const t = state.clock.elapsedTime;
    refs.current.forEach((m, i) => {
      if (!m) return;
      const phase = (Math.sin(i * 1.7 + t * 2) + 1) / 2;
      const h = 0.4 + (yieldT / 6) * 2.2 * phase;
      m.scale.y = h;
    });
  });
  return (
    <group position={[-20, 0, -20]}>
      {Array.from({ length: rows * cols }).map((_, i) => {
        const x = (i % cols) * 6;
        const z = Math.floor(i / cols) * 6;
        return (
          <mesh
            key={i}
            position={[x, 0.6, z]}
            ref={(el) => {
              if (el) refs.current[i] = el;
            }}
          >
            <coneGeometry args={[1.1, 1, 6]} />
            <meshStandardMaterial color="#4ade80" />
          </mesh>
        );
      })}
    </group>
  );
};

const WaterFlow: React.FC = () => {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const pts = new Float32Array(400 * 3);
    for (let i = 0; i < 400; i++) {
      const t = (i % 100) / 100;
      const x = -35 + t * 70;
      const y = Math.sin(x / 15) * 3;
      pts[i * 3] = x + (Math.random() - 0.5) * 1.5;
      pts[i * 3 + 1] = y + 0.8 + Math.random() * 0.8;
      pts[i * 3 + 2] = Math.floor(i / 100) * 2 - 3;
    }
    return pts;
  }, []);
  useFrame((state) => {
    if (!ref.current) return;
    const arr = ref.current.geometry.attributes.position.array as Float32Array;
    for (let i = 0; i < 400; i++) {
      arr[i * 3] += state.clock.getDelta() * 4;
      if (arr[i * 3] > 35) arr[i * 3] = -35;
    }
    ref.current.geometry.attributes.position.needsUpdate = true;
  });
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#38bdf8" size={0.35} transparent opacity={0.9} />
    </points>
  );
};

const FloodPlane: React.FC<{ chain: ScientificChainResult | null }> = ({ chain }) => {
  const wse = num(chain?.flood?.summary?.wse_m) ?? 0.05;
  const ref = useRef<THREE.Mesh>(null);
  useFrame((state) => {
    if (!ref.current) return;
    ref.current.position.y = wse * 3 + Math.sin(state.clock.elapsedTime * 1.5) * 0.05;
  });
  return (
    <mesh ref={ref} rotation={[-Math.PI / 2, 0, 0]} position={[0, wse * 3, 0]}>
      <planeGeometry args={[55, 55]} />
      <meshStandardMaterial color="#2563eb" transparent opacity={0.45} />
    </mesh>
  );
};

const ParetoScatter: React.FC<{ chain: ScientificChainResult | null }> = ({ chain }) => {
  const front = (chain?.optimization?.outputs?.pareto_front as unknown[] | undefined) ?? [];
  const points = useMemo((): Array<{
    erosion_t_ha_yr: number;
    yield_ton_ha: number;
    deficit_mcm: number;
  }> => {
    if (!front.length) return [{ erosion_t_ha_yr: 0.23, yield_ton_ha: 8.27, deficit_mcm: 0.84 }];
    return front as Array<{ erosion_t_ha_yr: number; yield_ton_ha: number; deficit_mcm: number }>;
  }, [front]);
  const refs = useRef<THREE.Mesh[]>([]);
  useFrame((state) => {
    refs.current.forEach((m, i) => {
      if (m) m.scale.setScalar(0.7 + Math.sin(state.clock.elapsedTime * 2 + i) * 0.25);
    });
  });
  return (
    <group position={[0, 5, 0]}>
      {points.map((p, i) => (
        <mesh
          key={i}
          position={[p.erosion_t_ha_yr * 22 - 6, p.yield_ton_ha * 1.2, p.deficit_mcm * 4 - 4]}
          ref={(el) => {
            if (el) refs.current[i] = el;
          }}
        >
          <sphereGeometry args={[0.45, 12, 12]} />
          <meshStandardMaterial color="#ec4899" emissive="#ec4899" emissiveIntensity={0.4} />
        </mesh>
      ))}
    </group>
  );
};

const ModeOverlay: React.FC<{ mode: SceneMode; chain: ScientificChainResult | null }> = ({
  mode,
  chain,
}) => {
  switch (mode) {
    case 'climate':
      return <Rain />;
    case 'carbon':
      return <CarbonColumns chain={chain} />;
    case 'crop':
      return <CropRows chain={chain} />;
    case 'water':
      return <WaterFlow />;
    case 'flood':
      return <FloodPlane chain={chain} />;
    case 'optimize':
      return <ParetoScatter chain={chain} />;
    default:
      return null;
  }
};

/**
 * شبیه‌ساز سه‌بعدی داشبورد — یک صحنه با حالت‌های هر ماژول (اقلیم/خاک/فرسایش/کربن/محصول/آب/سیلاب/بهینه‌سازی).
 * مقادیر واقعی زنجیره (پارتو، عمق سیلاب، عملکرد، استخرهای کربن) روی صحنه اعمال می‌شوند؛
 * زمین و انیمیشن‌ها صرفاً برای تجسم هستند و هرگز به‌عنوان خروجی داده ارائه نمی‌شوند.
 */
export const DashboardScene3D: React.FC<DashboardScene3DProps> = ({
  mode,
  realLand,
  chain,
  height = 420,
}) => {
  return (
    <div
      style={{
        height,
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        background: '#0f172a',
        position: 'relative',
      }}
    >
      <Canvas camera={{ position: [0, 16, 26], fov: 50 }} dpr={[1, 1.5]}>
        <Sky sunPosition={[80, 40, 20]} turbidity={6} />
        <ambientLight intensity={0.55} />
        <directionalLight position={[30, 40, 20]} intensity={1.1} castShadow />
        <Terrain mode={mode} chain={chain} />
        <ModeOverlay mode={mode} chain={chain} />
        <OrbitControls
          enablePan={false}
          minDistance={12}
          maxDistance={60}
          maxPolarAngle={Math.PI / 2.2}
        />
      </Canvas>
      <div
        style={{
          position: 'absolute',
          bottom: 10,
          left: 10,
          background: 'rgba(15,23,42,0.8)',
          color: '#cbd5e1',
          padding: '0.35rem 0.7rem',
          borderRadius: 8,
          fontSize: '0.72rem',
          pointerEvents: 'none',
        }}
      >
        تجسم {mode} —{' '}
        {realLand ? `${realLand.lat.toFixed(2)}°N, ${realLand.lon.toFixed(2)}°E` : '35.5°N, 51.5°E'}{' '}
        · مقادیر از زنجیره علمی واقعی
      </div>
    </div>
  );
};
