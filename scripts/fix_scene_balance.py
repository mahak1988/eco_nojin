#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scene Balance Fix: Single Source of Truth for terrain height
=============================================================
1. terrainHeight.ts - shared height function (farm valley + far mountains)
2. All 16 scene components grounded to real terrain height
3. Sky fixed (distance < camera.far), no background override
4. ContactShadows removed (gray sheet)
5. GodRays rebuilt as subtle vertical light shafts
6. Lake/river/shore placed at basin level
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
SRC = FRONTEND / "src"
SIM = SRC / "components" / "cinematic"
UTILS = SRC / "utils"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def err(m): print(f"[ERROR] {m}")


def setup_git_path():
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


# =============================================================================
# 1. SHARED TERRAIN HEIGHT (Single Source of Truth)
# =============================================================================

TERRAIN_HEIGHT = r'''// Single Source of Truth for terrain elevation.
// EVERY component (terrain, grass, animals, water, structures) MUST use this.

class PerlinNoise {
  private p: number[];
  constructor(seed = 42) {
    this.p = [];
    for (let i = 0; i < 256; i++) this.p[i] = i;
    let n = seed;
    for (let i = 255; i > 0; i--) {
      n = (n * 9301 + 49297) % 233280;
      const j = Math.floor((n / 233280) * (i + 1));
      [this.p[i], this.p[j]] = [this.p[j], this.p[i]];
    }
    for (let i = 0; i < 256; i++) this.p[256 + i] = this.p[i];
  }
  private fade(t: number) { return t * t * t * (t * (t * 6 - 15) + 10); }
  private lerp(t: number, a: number, b: number) { return a + t * (b - a); }
  private grad(h: number, x: number, y: number) {
    const g = h & 7;
    const u = g < 4 ? x : y;
    const v = g < 4 ? y : x;
    return ((g & 1) ? -u : u) + ((g & 2) ? -v : v);
  }
  noise2D(x: number, y: number): number {
    const X = Math.floor(x) & 255, Y = Math.floor(y) & 255;
    x -= Math.floor(x); y -= Math.floor(y);
    const u = this.fade(x), v = this.fade(y);
    const A = this.p[X] + Y, B = this.p[X + 1] + Y;
    return this.lerp(v,
      this.lerp(u, this.grad(this.p[A], x, y), this.grad(this.p[B], x - 1, y)),
      this.lerp(u, this.grad(this.p[A + 1], x, y - 1), this.grad(this.p[B + 1], x - 1, y - 1)));
  }
  fbm(x: number, y: number, oct = 4): number {
    let t = 0, f = 1, a = 1, m = 0;
    for (let i = 0; i < oct; i++) { t += this.noise2D(x * f, y * f) * a; m += a; a *= 0.5; f *= 2; }
    return t / m;
  }
  ridged(x: number, y: number, oct = 4): number {
    let t = 0, f = 1, a = 1, m = 0;
    for (let i = 0; i < oct; i++) {
      const n = 1 - Math.abs(this.noise2D(x * f, y * f));
      t += n * n * a; m += a; a *= 0.5; f *= 2;
    }
    return t / m;
  }
}

export const perlin = new PerlinNoise(42);
export const TERRAIN_SIZE = 800;
export const LAKE_LEVEL = -1.3;

function smoothstep(e0: number, e1: number, x: number): number {
  const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0)));
  return t * t * (3 - 2 * t);
}

/**
 * World-space terrain height.
 * Design: flat farm valley at center (±1.5m), mountains at horizon (up to 45m).
 */
export function getTerrainHeight(x: number, z: number): number {
  const nx = x / TERRAIN_SIZE;
  const nz = z / TERRAIN_SIZE;

  // Far zone: mountains + hills
  const mountains = perlin.ridged(nx * 3 + 10, nz * 3 + 10, 4) * 40;
  const hills = perlin.fbm(nx * 5, nz * 5, 4) * 15;
  const detail = perlin.fbm(nx * 20, nz * 20, 3) * 2;
  const mountainous = mountains + hills + detail;

  // Near zone: gentle farm valley
  const farm = perlin.fbm(nx * 8, nz * 8, 2) * 1.5 + perlin.fbm(nx * 30, nz * 30, 2) * 0.3;

  const dist = Math.sqrt(x * x + z * z);
  const t = smoothstep(70, 240, dist);
  let h = farm * (1 - t) + mountainous * t;

  // Lake basin carve near center
  const lakeMask = Math.max(0, perlin.noise2D(nx * 2 + 5, nz * 2 + 5));
  h -= Math.pow(1 - lakeMask, 3) * 2.5 * (1 - t);

  return h;
}
'''


# =============================================================================
# 2. TERRAIN (uses shared height)
# =============================================================================

TERRAIN = r'''import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight, TERRAIN_SIZE, perlin } from '../../utils/terrainHeight';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function Terrain() {
  const { condition } = useWeatherStore();
  const SEGMENTS = 256;

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(TERRAIN_SIZE, TERRAIN_SIZE, SEGMENTS, SEGMENTS);
    const pos = geo.attributes.position;
    const colors = new Float32Array(pos.count * 3);

    for (let i = 0; i < pos.count; i++) {
      const px = pos.getX(i);
      const py = pos.getY(i);
      const wx = px;          // world x
      const wz = -py;         // world z after rotateX(-PI/2)
      const h = getTerrainHeight(wx, wz);
      pos.setZ(i, h);

      const nx = wx / TERRAIN_SIZE, nz = wz / TERRAIN_SIZE;
      const var1 = perlin.fbm(nx * 40, nz * 40, 2) * 0.06;
      let r, g, b;

      if (h < -1.8)      { r = 0.16; g = 0.12; b = 0.08; }              // lake bed
      else if (h < -0.6) { r = 0.60 + var1; g = 0.50 + var1; b = 0.33; } // sand shore
      else if (h < 2)    { r = 0.20 + var1; g = 0.47 + var1 * 2; b = 0.14; } // lush grass
      else if (h < 8)    { r = 0.28 + var1; g = 0.52 + var1; b = 0.20; } // grass
      else if (h < 18)   { r = 0.42 + var1; g = 0.40 + var1; b = 0.28; } // dry grass/rock
      else if (h < 30)   { r = 0.47 + var1; g = 0.44 + var1; b = 0.40; } // rock
      else {
        const s = Math.min(1, (h - 30) / 8);
        r = 0.5 + s * 0.42; g = 0.48 + s * 0.45; b = 0.45 + s * 0.5;    // snow
      }
      colors[i * 3] = r; colors[i * 3 + 1] = g; colors[i * 3 + 2] = b;
    }

    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    geo.rotateX(-Math.PI / 2);
    return geo;
  }, []);

  const overlay = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#c4a574');
    if (condition === 'snow') return new THREE.Color('#e8e8f0');
    return null;
  }, [condition]);

  return (
    <mesh geometry={geometry} receiveShadow castShadow>
      <meshStandardMaterial
        vertexColors
        roughness={0.88}
        metalness={0.02}
        color={overlay || '#ffffff'}
      />
    </mesh>
  );
}
'''


# =============================================================================
# 3. LIGHTING (Sky visible, no background override)
# =============================================================================

LIGHTING = r'''import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function LightingSystem() {
  const sunRef = useRef<THREE.DirectionalLight>(null);
  const { timeOfDay, sunPosition, condition, intensity } = useWeatherStore();

  // Fog ONLY (never override scene.background - let Sky render!)
  useFrame(({ scene }) => {
    if (!scene.fog) scene.fog = new THREE.FogExp2('#cfe0ee', 0.0012);
    const fog = scene.fog as THREE.FogExp2;

    let density = 0.0012;
    let color = '#cfe0ee';

    if (condition === 'dust')       { density = 0.016 + intensity * 0.015; color = '#a08055'; }
    else if (condition === 'storm') { density = 0.012 + intensity * 0.012; color = '#5a6675'; }
    else if (condition === 'rain')  { density = 0.005; color = '#93a5b5'; }
    else if (condition === 'snow')  { density = 0.005; color = '#dfe5ee'; }
    else if (condition === 'drought'){ density = 0.0025; color = '#d8c49a'; }
    else if (timeOfDay === 'night') { density = 0.0015; color = '#0a1520'; }
    else if (timeOfDay === 'dawn')  { density = 0.002; color = '#ffd9b0'; }
    else if (timeOfDay === 'dusk')  { density = 0.002; color = '#ffc9a0'; }

    fog.density += (density - fog.density) * 0.06;
    fog.color.lerp(new THREE.Color(color), 0.06);
  });

  const sunIntensity = (() => {
    let base = 2.2;
    if (timeOfDay === 'night') base = 0.15;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 1.1;
    if (condition === 'dust') base *= 0.25;
    if (condition === 'storm') base *= 0.18;
    if (condition === 'rain') base *= 0.5;
    if (condition === 'snow') base *= 0.7;
    return base;
  })();

  const sunColor = (() => {
    if (condition === 'dust') return '#d4935a';
    if (condition === 'storm') return '#8a9aa8';
    if (timeOfDay === 'dawn') return '#ffb347';
    if (timeOfDay === 'dusk') return '#ff6b6b';
    if (timeOfDay === 'night') return '#4a6fa5';
    return '#fff8e7';
  })();

  return (
    <>
      <directionalLight
        ref={sunRef}
        position={sunPosition}
        intensity={sunIntensity}
        color={sunColor}
        castShadow
        shadow-mapSize={[4096, 4096]}
        shadow-camera-left={-400}
        shadow-camera-right={400}
        shadow-camera-top={400}
        shadow-camera-bottom={-400}
        shadow-camera-near={1}
        shadow-camera-far={1500}
        shadow-bias={-0.0001}
        shadow-normalBias={0.05}
      />
      <ambientLight intensity={timeOfDay === 'night' ? 0.2 : condition === 'dust' || condition === 'storm' ? 0.25 : 0.45} color={sunColor} />
      <hemisphereLight
        args={[
          condition === 'dust' ? '#8b6f47' : '#b8d4e8',
          '#4a7c3a',
          condition === 'dust' || condition === 'storm' ? 0.25 : 0.5,
        ]}
      />

      {/* CRITICAL FIX: distance must be < camera.far (5000) or Sky is clipped! */}
      {timeOfDay !== 'night' && (
        <Sky
          distance={3500}
          sunPosition={sunPosition}
          mieCoefficient={condition === 'dust' ? 0.12 : condition === 'storm' ? 0.08 : 0.005}
          rayleigh={condition === 'dust' ? 6 : condition === 'storm' ? 4 : 1.5}
          turbidity={condition === 'dust' ? 18 : condition === 'storm' ? 12 : 6}
        />
      )}

      {timeOfDay === 'night' && <Stars radius={800} depth={100} count={8000} factor={6} saturation={0.2} fade speed={0.5} />}

      {(condition === 'storm' || condition === 'rain') && (
        <>
          <Cloud position={[-60, 80, -100]} speed={0.6} opacity={0.9} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} segments={40} />
          <Cloud position={[80, 90, -120]} speed={0.5} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} segments={40} />
          <Cloud position={[0, 85, -150]} speed={0.7} opacity={0.95} color={condition === 'storm' ? '#1a202c' : '#6a7a88'} segments={40} />
        </>
      )}
      {condition === 'dust' && (
        <>
          <Cloud position={[-40, 25, -50]} speed={0.8} opacity={0.6} color="#8b6f47" segments={30} />
          <Cloud position={[60, 30, -70]} speed={0.9} opacity={0.7} color="#a0826b" segments={30} />
        </>
      )}
    </>
  );
}
'''


# =============================================================================
# 4. SIMULATOR (ContactShadows removed)
# =============================================================================

SIMULATOR = r'''import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Preload } from '@react-three/drei';
import * as THREE from 'three';
import { Terrain } from './Terrain';
import { WeatherEffects } from './WeatherEffects';
import { VegetationSystem } from './VegetationSystem';
import { LightingSystem } from './LightingSystem';
import { PostProcessing } from './PostProcessing';
import { WaterSystem } from './WaterSystem';
import { WeatherControls } from './WeatherControls';
import { Aurora } from './Aurora';
import { Lightning } from './Lightning';
import { Rainbow } from './Rainbow';
import { Fireflies } from './Fireflies';
import { Birds } from './Birds';
import { Butterflies } from './Butterflies';
import { GodRays } from './GodRays';
import { CinematicCamera } from './CinematicCamera';
import { CinematicOverlay } from './CinematicOverlay';
import { SeasonController } from './SeasonController';
import { InsectsSystem } from './InsectsSystem';
import { DomesticAnimals } from './DomesticAnimals';
import { Poultry } from './Poultry';
import { FloodSimulation } from './FloodSimulation';
import { IrrigationSystem } from './IrrigationSystem';
import { WellSystem } from './WellSystem';
import { RiverSystem } from './RiverSystem';
import { Coastline } from './Coastline';
import { WatershedEngineering } from './WatershedEngineering';
import { PlowingTrails } from './PlowingTrails';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';

function Scene() {
  const { condition, timeOfDay } = useWeatherStore();
  const a = useArtisticStore();

  return (
    <>
      <SeasonController />
      <CinematicCamera />
      <LightingSystem />
      <Terrain />
      <VegetationSystem />
      <WeatherEffects />
      {!a.enableFlood && <WaterSystem />}
      <PostProcessing />

      {a.enableAurora && timeOfDay === 'night' && <Aurora />}
      {condition === 'storm' && <Lightning />}
      {a.enableRainbow && (condition === 'rain' || condition === 'clear') && timeOfDay === 'day' && <Rainbow />}
      {a.enableFireflies && timeOfDay === 'night' && <Fireflies />}
      {a.enableBirds && timeOfDay !== 'night' && condition !== 'storm' && condition !== 'dust' && <Birds />}
      {a.enableButterflies && timeOfDay === 'day' && condition === 'clear' && <Butterflies />}
      {a.enableGodRays && timeOfDay !== 'night' && condition !== 'dust' && condition !== 'storm' && <GodRays />}

      {a.enableInsects && <InsectsSystem />}
      {a.enableDomesticAnimals && <DomesticAnimals />}
      {a.enablePoultry && <Poultry />}
      {a.enableFlood && <FloodSimulation />}
      {a.enableIrrigation && <IrrigationSystem />}
      {a.enableWell && <WellSystem />}
      {a.enableRiver && <RiverSystem />}
      {a.enableCoastline && <Coastline />}
      {a.enableWatershed && <WatershedEngineering />}
      {a.enablePlowing && <PlowingTrails />}

      {/* NOTE: ContactShadows REMOVED - it created a gray sheet over valleys.
          Real shadow maps (4096 PCF) are enough. */}

      <OrbitControls
        makeDefault
        enablePan
        enableZoom
        enableRotate
        minDistance={20}
        maxDistance={600}
        maxPolarAngle={Math.PI / 2.08}
        target={[0, 2, 0]}
        enableDamping
        dampingFactor={0.05}
      />
      <Preload all />
    </>
  );
}

export function CinematicSimulator() {
  const { timeOfDay, condition } = useWeatherStore();

  const exposure = (() => {
    let base = 1.1;
    if (timeOfDay === 'night') base = 0.6;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 0.95;
    if (condition === 'dust') base *= 0.55;
    if (condition === 'storm') base *= 0.45;
    return base;
  })();

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#000' }}>
      <Canvas
        shadows
        camera={{ position: [120, 60, 120], fov: 60, near: 0.5, far: 8000 }}
        gl={{ antialias: true, powerPreference: 'high-performance' }}
        dpr={[1.5, 2]}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = exposure;
          gl.outputColorSpace = THREE.SRGBColorSpace;
          gl.shadowMap.enabled = true;
          gl.shadowMap.type = THREE.PCFSoftShadowMap;
        }}
      >
        <Suspense fallback={null}>
          <Scene />
        </Suspense>
      </Canvas>
      <CinematicOverlay />
      <WeatherControls />
    </div>
  );
}

export default CinematicSimulator;
'''


# =============================================================================
# 5. GOD RAYS (subtle vertical shafts, grounded)
# =============================================================================

GODRAYS = r'''import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

/** Subtle vertical light shafts over the farm valley (not a floating fan!). */
export function GodRays() {
  const shafts = useMemo(() => {
    const arr = [];
    for (let i = 0; i < 9; i++) {
      const angle = (i / 9) * Math.PI * 2;
      const r = 18 + (i % 3) * 9;
      const x = Math.cos(angle) * r;
      const z = Math.sin(angle) * r;
      const h = getTerrainHeight(x, z);
      arr.push({ x, z, y: h + 18, tilt: (i % 2 === 0 ? 1 : -1) * 0.06, radius: 1.2 + (i % 3) * 0.7 });
    }
    return arr;
  }, []);

  return (
    <group>
      {shafts.map((s, i) => (
        <mesh key={i} position={[s.x, s.y, s.z]} rotation={[s.tilt, 0, s.tilt]}>
          <cylinderGeometry args={[s.radius * 0.4, s.radius, 36, 8, 1, true]} />
          <meshBasicMaterial
            color="#fff4c8"
            transparent
            opacity={0.055}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
    </group>
  );
}
'''


# =============================================================================
# 6. VEGETATION (grounded grass)
# =============================================================================

VEGETATION = r'''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';
import { useWeatherStore } from '../../hooks/useWeatherStore';

const grassVertex = `
  uniform float uTime;
  uniform float uWindStrength;
  uniform float uGrowthStage;
  attribute float aRandom;
  varying float vHeight;
  varying float vRandom;
  void main() {
    vHeight = position.y;
    vRandom = aRandom;
    vec4 worldPos = instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0);
    float sway = sin(uTime * 2.0 + worldPos.x * 0.35 + aRandom * 6.28) * position.y * position.y * uWindStrength;
    float swayZ = cos(uTime * 1.7 + worldPos.z * 0.35 + aRandom * 6.28) * position.y * position.y * uWindStrength * 0.6;
    vec3 displaced = position;
    displaced.x += sway;
    displaced.z += swayZ;
    displaced.y *= (0.3 + uGrowthStage * 0.7);
    vec4 mvPosition = modelViewMatrix * instanceMatrix * vec4(displaced, 1.0);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const grassFragment = `
  uniform vec3 uBaseColor;
  uniform vec3 uTipColor;
  varying float vHeight;
  varying float vRandom;
  void main() {
    vec3 color = mix(uBaseColor, uTipColor, clamp(vHeight, 0.0, 1.0));
    color *= 0.85 + vRandom * 0.3;
    gl_FragColor = vec4(color, 1.0);
  }
`;

export function VegetationSystem() {
  const count = 8000;
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  const { windSpeed, condition, plantGrowthStage } = useWeatherStore();

  const blade = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const v = new Float32Array([-0.05, 0, 0, 0.05, 0, 0, 0.03, 0.5, 0, -0.03, 0.5, 0, 0, 1, 0]);
    const idx = new Uint16Array([0, 1, 2, 0, 2, 3, 3, 2, 4]);
    g.setAttribute('position', new THREE.BufferAttribute(v, 3));
    g.setIndex(new THREE.BufferAttribute(idx, 1));
    g.computeVertexNormals();
    return g;
  }, []);

  const randoms = useMemo(() => {
    const r = new Float32Array(count);
    const dummy = new THREE.Object3D();
    // We need meshRef ready; instead store transforms and apply in effect below
    for (let i = 0; i < count; i++) r[i] = Math.random();
    return r;
  }, []);

  const transforms = useMemo(() => {
    const list: { x: number; y: number; z: number; rot: number; scale: number }[] = [];
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.sqrt(Math.random()) * 110; // farm zone + a bit beyond
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const y = getTerrainHeight(x, z);
      if (y < -1.0) continue; // no grass under water
      list.push({ x, y, z, rot: Math.random() * Math.PI, scale: 0.7 + Math.random() * 0.9 });
    }
    return list;
  }, []);

  useMemo(() => {
    if (!meshRef.current) return;
    const dummy = new THREE.Object3D();
    transforms.forEach((t, i) => {
      dummy.position.set(t.x, t.y - 0.05, t.z);
      dummy.rotation.set(0, t.rot, 0);
      dummy.scale.setScalar(t.scale);
      dummy.updateMatrix();
      meshRef.current!.setMatrixAt(i, dummy.matrix);
    });
    meshRef.current.instanceMatrix.needsUpdate = true;
  }, [transforms]);

  const baseColor = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#8b6f47');
    if (condition === 'snow') return new THREE.Color('#d4d4dc');
    return new THREE.Color('#2d5a3d');
  }, [condition]);

  const tipColor = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#a0845a');
    if (condition === 'snow') return new THREE.Color('#ffffff');
    return new THREE.Color('#3d7a4f').lerp(new THREE.Color('#7cb342'), plantGrowthStage);
  }, [condition, plantGrowthStage]);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
      materialRef.current.uniforms.uWindStrength.value = windSpeed * 0.02;
      materialRef.current.uniforms.uGrowthStage.value = plantGrowthStage;
      materialRef.current.uniforms.uBaseColor.value = baseColor;
      materialRef.current.uniforms.uTipColor.value = tipColor;
    }
  });

  return (
    <instancedMesh ref={meshRef} args={[blade, undefined, count]} castShadow>
      <shaderMaterial
        ref={materialRef}
        vertexShader={grassVertex}
        fragmentShader={grassFragment}
        uniforms={{
          uTime: { value: 0 },
          uWindStrength: { value: 0.3 },
          uGrowthStage: { value: 0.5 },
          uBaseColor: { value: baseColor },
          uTipColor: { value: tipColor },
        }}
        side={THREE.DoubleSide}
      />
      <instancedBufferAttribute attach="attributes-aRandom" args={[randoms, 1]} />
    </instancedMesh>
  );
}
'''


# =============================================================================
# 7. ANIMALS / POULTRY / INSECTS (grounded)
# =============================================================================

ANIMALS = r'''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

function Animal({ color, size = 1 }: { color: string; size?: number }) {
  return (
    <group scale={size}>
      <mesh position={[0, 0.8, 0]} castShadow><boxGeometry args={[1.5, 0.8, 0.7]} /><meshStandardMaterial color={color} /></mesh>
      <mesh position={[0.8, 1.1, 0]} castShadow><boxGeometry args={[0.5, 0.5, 0.5]} /><meshStandardMaterial color={color} /></mesh>
      {[[-0.5, 0.4, -0.2], [-0.5, 0.4, 0.2], [0.5, 0.4, -0.2], [0.5, 0.4, 0.2]].map((p, i) => (
        <mesh key={i} position={p as [number, number, number]} castShadow><boxGeometry args={[0.15, 0.8, 0.15]} /><meshStandardMaterial color="#2d3436" /></mesh>
      ))}
    </group>
  );
}

export function DomesticAnimals() {
  const groupRef = useRef<THREE.Group>(null);

  const animals = useMemo(() => {
    const list = [];
    const mk = (type: string, color: string, size: number, x: number, z: number, speed: number) =>
      list.push({ type, color, size, x, z, h: getTerrainHeight(x, z), speed, phase: Math.random() * Math.PI * 2 });
    for (let i = 0; i < 5; i++) mk('cow', i % 2 ? '#8b4513' : '#f5f0e8', 1.2, 25 + Math.random() * 25, -15 + Math.random() * 30, 0.05 + Math.random() * 0.05);
    for (let i = 0; i < 8; i++) mk('sheep', '#f5f5dc', 0.8, -30 + Math.random() * 22, 12 + Math.random() * 25, 0.08 + Math.random() * 0.05);
    for (let i = 0; i < 3; i++) mk('horse', '#6b3e2a', 1.5, 40 + Math.random() * 15, 25 + Math.random() * 15, 0.1 + Math.random() * 0.1);
    return list;
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((g, i) => {
      const a = animals[i];
      const tt = t * a.speed + a.phase;
      const x = a.x + Math.sin(tt) * 6;
      const z = a.z + Math.cos(tt * 0.8) * 6;
      g.position.set(x, getTerrainHeight(x, z), z);
      g.rotation.y = tt + Math.PI / 2;
    });
  });

  return (
    <group ref={groupRef}>
      {animals.map((a, i) => <group key={i}><Animal color={a.color} size={a.size} /></group>)}
    </group>
  );
}
'''

POULTRY = r'''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

export function Poultry() {
  const groupRef = useRef<THREE.Group>(null);

  const birds = useMemo(() => {
    const list = [];
    for (let i = 0; i < 12; i++) {
      const x = -8 + Math.random() * 18, z = 18 + Math.random() * 14;
      list.push({ color: i % 3 === 0 ? '#8b4513' : i % 3 === 1 ? '#ffffff' : '#d4a574', size: 0.4, x, z, h: getTerrainHeight(x, z), phase: Math.random() * 6.28, speed: 0.2 + Math.random() * 0.2 });
    }
    for (let i = 0; i < 5; i++) {
      const x = -20 + Math.random() * 10, z = -8 + Math.random() * 8;
      list.push({ color: '#f4d03f', size: 0.35, x, z, h: getTerrainHeight(x, z), phase: Math.random() * 6.28, speed: 0.15 + Math.random() * 0.15 });
    }
    return list;
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((g, i) => {
      const b = birds[i];
      const x = b.x + Math.sin(t * b.speed + b.phase) * 3;
      const z = b.z + Math.cos(t * b.speed * 0.8 + b.phase) * 3;
      g.position.set(x, getTerrainHeight(x, z) + Math.abs(Math.sin(t * 4 + b.phase)) * 0.15, z);
      g.rotation.y = t * b.speed;
    });
  });

  return (
    <group ref={groupRef}>
      {birds.map((b, i) => (
        <group key={i} scale={b.size}>
          <mesh position={[0, 0.4, 0]} castShadow><sphereGeometry args={[0.5, 8, 6]} /><meshStandardMaterial color={b.color} /></mesh>
          <mesh position={[0.3, 0.7, 0]} castShadow><sphereGeometry args={[0.25, 8, 6]} /><meshStandardMaterial color={b.color} /></mesh>
          <mesh position={[0.55, 0.7, 0]}><coneGeometry args={[0.08, 0.15, 4]} /><meshStandardMaterial color="#ff6b00" /></mesh>
        </group>
      ))}
    </group>
  );
}
'''

INSECTS = r'''import { useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

export function InsectsSystem() {
  const groupRef = useRef<THREE.Group>(null);

  const insects = useMemo(() => {
    const list = [];
    const mk = (color: string, size: number, n: number, hMin: number, hMax: number, speed: number) => {
      for (let i = 0; i < n; i++) {
        const x = (Math.random() - 0.5) * 90;
        const z = (Math.random() - 0.5) * 90;
        const base = getTerrainHeight(x, z);
        list.push({ color, size, x, z, base, hOff: hMin + Math.random() * (hMax - hMin), phase: Math.random() * 6.28, speed });
      }
    };
    mk('#ffcc00', 0.15, 20, 1, 3, 0.8);   // bees
    mk('#d63031', 0.12, 15, 0.4, 1.2, 0.3); // ladybugs
    mk('#6c5b3c', 0.2, 8, 1.5, 4, 1.2);  // locusts
    return list;
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((m, i) => {
      const ins = insects[i];
      const tt = t * ins.speed + ins.phase;
      m.position.set(
        ins.x + Math.sin(tt) * 4,
        ins.base + ins.hOff + Math.sin(tt * 2) * 0.4,
        ins.z + Math.cos(tt * 0.7) * 4
      );
      m.rotation.y = tt;
    });
  });

  return (
    <group ref={groupRef}>
      {insects.map((ins, i) => (
        <mesh key={i}><sphereGeometry args={[ins.size, 6, 5]} /><meshStandardMaterial color={ins.color} /></mesh>
      ))}
    </group>
  );
}
'''


# =============================================================================
# 8. WATER / RIVER / SHORE (basin level)
# =============================================================================

WATER = r'''import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { CustomWater } from './CustomWater';
import { LAKE_LEVEL } from '../../utils/terrainHeight';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function WaterSystem() {
  const { condition, timeOfDay } = useWeatherStore();

  const waterColor = (() => {
    if (condition === 'drought') return '#8b7355';
    if (condition === 'dust') return '#a0826b';
    if (timeOfDay === 'dawn') return '#ff9a6b';
    if (timeOfDay === 'dusk') return '#d85a7a';
    if (timeOfDay === 'night') return '#1a2a4a';
    return '#2a5a8a';
  })();

  const waveHeight = condition === 'storm' ? 0.5 : condition === 'rain' ? 0.3 : 0.15;

  return (
    <group>
      {/* Central lake at basin level */}
      <CustomWater
        position={[0, LAKE_LEVEL, 0]}
        args={[110, 110]}
        color={waterColor}
        waveHeight={waveHeight}
        waveSpeed={condition === 'storm' ? 1.2 : 0.5}
        segments={96}
      />
    </group>
  );
}
'''

RIVER = r'''import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { LAKE_LEVEL } from '../../utils/terrainHeight';

/** Inflow stream feeding the lake, kept inside the flat basin. */
export function RiverSystem() {
  const matRef = useRef<THREE.ShaderMaterial>(null);

  useFrame((state) => {
    if (matRef.current) matRef.current.uniforms.uTime.value = state.clock.elapsedTime;
  });

  return (
    <mesh position={[55, LAKE_LEVEL + 0.15, -20]} rotation={[-Math.PI / 2, 0, -0.4]}>
      <planeGeometry args={[90, 5, 32, 4]} />
      <shaderMaterial
        ref={matRef}
        transparent
        uniforms={{ uTime: { value: 0 } }}
        vertexShader={`
          varying vec2 vUv;
          void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
        `}
        fragmentShader={`
          uniform float uTime;
          varying vec2 vUv;
          void main() {
            float flow = fract(vUv.x * 6.0 - uTime * 0.6);
            vec3 color = mix(vec3(0.12, 0.32, 0.52), vec3(0.3, 0.6, 0.8), flow);
            float edge = smoothstep(0.0, 0.15, vUv.y) * smoothstep(1.0, 0.85, vUv.y);
            gl_FragColor = vec4(color, 0.85 * edge);
          }
        `}
      />
    </mesh>
  );
}
'''

SHORE = r'''import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight, LAKE_LEVEL } from '../../utils/terrainHeight';

/** Sandy shore ring around the lake. */
export function Coastline() {
  const ring = useMemo(() => {
    const pts: { x: number; z: number; y: number; rot: number }[] = [];
    for (let i = 0; i < 24; i++) {
      const a = (i / 24) * Math.PI * 2;
      const r = 56 + Math.sin(i * 3.7) * 4;
      const x = Math.cos(a) * r;
      const z = Math.sin(a) * r;
      pts.push({ x, z, y: Math.max(getTerrainHeight(x, z), LAKE_LEVEL + 0.25), rot: -a });
    }
    return pts;
  }, []);

  return (
    <group>
      {ring.map((p, i) => (
        <mesh key={i} position={[p.x, p.y, p.z]} rotation={[-Math.PI / 2, 0, p.rot]} receiveShadow>
          <planeGeometry args={[16, 7]} />
          <meshStandardMaterial color="#e8d5a6" roughness={0.95} />
        </mesh>
      ))}
    </group>
  );
}
'''


# =============================================================================
# 9. FARM STRUCTURES (grounded)
# =============================================================================

IRRIGATION = r'''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

function Sprinkler({ position }: { position: [number, number, number] }) {
  const sprayRef = useRef<THREE.Points>(null);
  const count = 250;
  const positions = useMemo(() => new Float32Array(count * 3), []);
  const velocities = useMemo(() => {
    const v = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const a = (i / count) * Math.PI * 2;
      v[i * 3] = Math.cos(a) * 0.3; v[i * 3 + 1] = 0.4 + Math.random() * 0.2; v[i * 3 + 2] = Math.sin(a) * 0.3;
    }
    return v;
  }, []);

  useFrame((state) => {
    if (!sprayRef.current) return;
    const attr = sprayRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = attr.array as Float32Array;
    const t = state.clock.elapsedTime;
    for (let i = 0; i < count; i++) {
      arr[i * 3] += velocities[i * 3] * 0.15;
      arr[i * 3 + 1] += velocities[i * 3 + 1] * 0.1 - 0.015;
      arr[i * 3 + 2] += velocities[i * 3 + 2] * 0.15;
      if (arr[i * 3 + 1] < 0) {
        const a = (i / count) * Math.PI * 2 + t * 2;
        const s = 0.3 + Math.random() * 0.3;
        arr[i * 3] = 0; arr[i * 3 + 1] = 2; arr[i * 3 + 2] = 0;
        velocities[i * 3] = Math.cos(a) * s; velocities[i * 3 + 2] = Math.sin(a) * s;
      }
    }
    attr.needsUpdate = true;
  });

  return (
    <group position={position}>
      <mesh position={[0, 1, 0]} castShadow><cylinderGeometry args={[0.08, 0.1, 2, 8]} /><meshStandardMaterial color="#2c3e50" metalness={0.8} /></mesh>
      <points ref={sprayRef} position={[0, 2, 0]}>
        <bufferGeometry><bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} /></bufferGeometry>
        <pointsMaterial size={0.1} color="#4fa3d1" transparent opacity={0.7} depthWrite={false} blending={THREE.AdditiveBlending} />
      </points>
    </group>
  );
}

export function IrrigationSystem() {
  const spots = useMemo(() => {
    const s: [number, number, number][] = [];
    [[-20, -20], [0, -20], [20, -20], [-20, 5], [0, 5], [20, 5]].forEach(([x, z]) => {
      s.push([x, getTerrainHeight(x, z), z]);
    });
    return s;
  }, []);

  return (
    <group>
      {spots.map((p, i) => <Sprinkler key={i} position={p} />)}
    </group>
  );
}
'''

WELL = r'''import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

export function WellSystem() {
  const h = useMemo(() => getTerrainHeight(35, -35), []);
  return (
    <group position={[35, h, -35]}>
      <mesh castShadow><cylinderGeometry args={[1.5, 1.8, 1.5, 16, 1, true]} /><meshStandardMaterial color="#8b7355" roughness={0.95} side={THREE.DoubleSide} /></mesh>
      <mesh position={[0, 0.8, 0]} castShadow><torusGeometry args={[1.6, 0.15, 8, 24]} /><meshStandardMaterial color="#6b5d47" /></mesh>
      <mesh position={[0, -0.6, 0]}><cylinderGeometry args={[1.4, 1.4, 0.1, 24]} /><meshStandardMaterial color="#2a5a8a" metalness={0.3} roughness={0.1} /></mesh>
      <mesh position={[0, 2, 0]} castShadow><boxGeometry args={[0.2, 3, 0.2]} /><meshStandardMaterial color="#5a3a20" /></mesh>
      <mesh position={[0, 3.5, 0]} castShadow><boxGeometry args={[3, 0.2, 0.2]} /><meshStandardMaterial color="#5a3a20" /></mesh>
    </group>
  );
}
'''

PLOWING = r'''import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

export function PlowingTrails() {
  const base = useMemo(() => getTerrainHeight(0, 45), []);
  const furrows = useMemo(() => Array.from({ length: 12 }, (_, i) => i * 3 - 16), []);

  return (
    <group position={[0, base + 0.05, 45]}>
      {furrows.map((z, i) => (
        <mesh key={i} position={[0, 0, z]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[50, 0.35]} />
          <meshStandardMaterial color="#4a3520" roughness={1} />
        </mesh>
      ))}
      {/* Tractor */}
      <group position={[15, 0.1, 0]}>
        <mesh position={[0, 1, 0]} castShadow><boxGeometry args={[2, 1.5, 1.2]} /><meshStandardMaterial color="#d63031" /></mesh>
        <mesh position={[-1.2, 1.2, 0]} castShadow><boxGeometry args={[0.8, 1, 1]} /><meshStandardMaterial color="#2d3436" /></mesh>
        {[[-0.8, 0.4, 0.7], [-0.8, 0.4, -0.7], [0.8, 0.6, 0.7], [0.8, 0.6, -0.7]].map((p, i) => (
          <mesh key={i} position={p as [number, number, number]} rotation={[Math.PI / 2, 0, 0]} castShadow>
            <cylinderGeometry args={[i < 2 ? 0.4 : 0.6, i < 2 ? 0.4 : 0.6, 0.3, 16]} />
            <meshStandardMaterial color="#1a1a1a" />
          </mesh>
        ))}
      </group>
    </group>
  );
}
'''

WATERSHED = r'''import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

function CheckDam({ x, z, width = 8 }: { x: number; z: number; width?: number }) {
  const h = useMemo(() => getTerrainHeight(x, z), [x, z]);
  return (
    <group position={[x, h + 0.4, z]}>
      <mesh castShadow receiveShadow><boxGeometry args={[width, 1.5, 1.5]} /><meshStandardMaterial color="#7d7468" roughness={1} /></mesh>
      <mesh position={[0, 0.1, -2.5]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width, 4]} />
        <meshStandardMaterial color="#2a5a8a" transparent opacity={0.7} />
      </mesh>
    </group>
  );
}

function Terrace({ x, z, level }: { x: number; z: number; level: number }) {
  const h = useMemo(() => getTerrainHeight(x, z), [x, z]);
  return (
    <group position={[x, h + level * 0.8, z]}>
      <mesh castShadow receiveShadow><boxGeometry args={[26, 0.5, 7]} /><meshStandardMaterial color="#6b5d3d" roughness={0.95} /></mesh>
      <mesh position={[0, 0.5, -3.7]} castShadow><boxGeometry args={[26, 1, 0.5]} /><meshStandardMaterial color="#8b7355" /></mesh>
      {Array.from({ length: 8 }).map((_, i) => (
        <mesh key={i} position={[(i - 3.5) * 3, 0.8, 0]} castShadow>
          <coneGeometry args={[0.3, 1.2, 6]} />
          <meshStandardMaterial color={level % 2 === 0 ? '#6ba368' : '#a8c686'} />
        </mesh>
      ))}
    </group>
  );
}

export function WatershedEngineering() {
  return (
    <group>
      <CheckDam x={-45} z={30} width={10} />
      <CheckDam x={-32} z={42} width={8} />
      <CheckDam x={-20} z={52} width={6} />
      <Terrace x={48} z={48} level={0} />
      <Terrace x={48} z={39} level={1} />
      <Terrace x={48} z={30} level={2} />
    </group>
  );
}
'''


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("")
    print("=" * 70)
    print("  🏗️ Scene Balance Fix: Single Source of Truth")
    print("=" * 70)
    print("")
    print("  Fixes:")
    print("    1. terrainHeight.ts - shared elevation for ALL components")
    print("    2. Farm valley design (flat center + mountains at horizon)")
    print("    3. Sky visible (distance 3500 < far 8000)")
    print("    4. ContactShadows removed (gray sheet)")
    print("    5. GodRays = subtle vertical shafts")
    print("    6. All animals/insects/structures grounded")
    print("    7. Lake/river/shore at basin level")
    print("")

    setup_git_path()

    print("[Step 1] Writing balanced scene components")
    print("-" * 70)
    files = {
        UTILS / "terrainHeight.ts": TERRAIN_HEIGHT,
        SIM / "Terrain.tsx": TERRAIN,
        SIM / "LightingSystem.tsx": LIGHTING,
        SIM / "CinematicSimulator.tsx": SIMULATOR,
        SIM / "GodRays.tsx": GODRAYS,
        SIM / "VegetationSystem.tsx": VEGETATION,
        SIM / "DomesticAnimals.tsx": ANIMALS,
        SIM / "Poultry.tsx": POULTRY,
        SIM / "InsectsSystem.tsx": INSECTS,
        SIM / "WaterSystem.tsx": WATER,
        SIM / "RiverSystem.tsx": RIVER,
        SIM / "Coastline.tsx": SHORE,
        SIM / "IrrigationSystem.tsx": IRRIGATION,
        SIM / "WellSystem.tsx": WELL,
        SIM / "PlowingTrails.tsx": PLOWING,
        SIM / "WatershedEngineering.tsx": WATERSHED,
    }
    for path, content in files.items():
        write_file(path, content)
        ok(f"Updated: {path.relative_to(SRC)}")
    print("")

    print("[Step 2] Building")
    print("-" * 70)
    result = subprocess.run("pnpm build", shell=True, cwd=FRONTEND,
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    build_ok = result.returncode == 0
    if build_ok:
        ok("🎉 Build successful!")
    else:
        err("Build failed:")
        for line in (result.stdout + result.stderr).splitlines()[-25:]:
            if line.strip():
                print(f"    {line}")
    print("")

    if build_ok:
        print("[Step 3] Committing")
        print("-" * 70)
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = ("fix(scene): balance & grounding - single source of truth for terrain height\\n\\n"
                   "Root causes fixed:\\n"
                   "- Sky clipped (distance > camera.far) -> white sky; now distance=3500, far=8000\\n"
                   "- scene.background override removed (Sky renders properly)\\n"
                   "- ContactShadows gray sheet removed\\n"
                   "- GodRays floating fan -> subtle vertical light shafts\\n"
                   "- ALL objects (grass, animals, insects, sprinklers, well, tractor,\\n"
                   "  check-dams, terraces) now sample getTerrainHeight(x,z)\\n"
                   "- Lake/river/shore placed at basin level (LAKE_LEVEL=-1.3)\\n"
                   "- Terrain redesigned: flat farm valley center + mountains at horizon\\n\\n"
                   "New shared util: src/utils/terrainHeight.ts (Perlin, fbm, ridged)\\n\\n"
                   "Visit: http://localhost:5173/hydroma")
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")

        print("")
        print("=" * 70)
        print("  🎉 SCENE BALANCED!")
        print("=" * 70)
        print("")
        print("  cd D:\\eco_nojin\\frontend && pnpm dev")
        print("  Visit: http://localhost:5173/hydroma")
        print("")
        print("  What you'll see now:")
        print("    🏔️ Mountains at horizon, flat farm valley in center")
        print("    🌊 Lake sitting naturally in the basin with sandy shore")
        print("    🐄 Animals walking ON the ground (not floating)")
        print("    🌾 Grass growing from real terrain height")
        print("    💧 Sprinklers & well grounded in the farm")
        print("    🚜 Tractor on the plowed field")
        print("    ☀️ Real blue sky with sun & soft shadows")
        print("    ✨ Subtle god-ray shafts (no more white fan)")
        print("")

    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())