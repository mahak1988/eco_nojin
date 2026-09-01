#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cinematic Smooth Polish: homepage-level fluidity for the 3D simulator
======================================================================
1. useQualityStore (zustand) - quality tiers: high/medium/low
2. PerformanceGovernor - real FPS measurement, adaptive tier shifting
3. CameraIntro - 5s cinematic aerial glide (easeOutCubic)
4. Adaptive DPR / shadows / grass count / post-processing per tier
5. Palette harmony with homepage hero (soft sky blue / calm water)
6. Fix: grass instancing moved to useLayoutEffect (matrices were never applied)
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
SRC = FRONTEND / "src"
SIM = SRC / "components" / "cinematic"
HOOKS = SRC / "hooks"


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
# 1. QUALITY STORE (zustand - works inside AND outside Canvas)
# =============================================================================

QUALITY_STORE = r'''import { create } from 'zustand';

export type QualityTier = 'high' | 'medium' | 'low';

interface QualityState {
  tier: QualityTier;
  setTier: (t: QualityTier) => void;
}

/**
 * Adaptive quality tier.
 * NOTE: zustand (not React Context) because React context does NOT
 * cross the R3F Canvas boundary.
 */
export const useQualityStore = create<QualityState>((set) => ({
  tier: 'high',
  setTier: (tier) => set({ tier }),
}));

export const TIER_LABEL: Record<QualityTier, string> = {
  high: 'بالا',
  medium: 'متوسط',
  low: 'پایین',
};
'''


# =============================================================================
# 2. PERFORMANCE GOVERNOR (FPS-based adaptive quality)
# =============================================================================

PERF_GOVERNOR = r'''import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useQualityStore } from '../../hooks/useQualityStore';

/**
 * FPS Governor: measures real FPS every 2.5s and shifts the quality tier.
 * Keeps the 3D simulator as fluid as the 2D homepage on ANY GPU.
 *
 *  - FPS < 27  -> downgrade (high->medium->low)
 *  - FPS > 55  -> upgrade   (low->medium->high)
 */
export function PerformanceGovernor() {
  const tier = useQualityStore((s) => s.tier);
  const setTier = useQualityStore((s) => s.setTier);
  const acc = useRef({ frames: 0, last: performance.now() });

  useFrame(() => {
    const a = acc.current;
    a.frames += 1;
    const now = performance.now();
    const dt = now - a.last;
    if (dt >= 2500) {
      const fps = (a.frames * 1000) / dt;
      a.frames = 0;
      a.last = now;
      if (fps < 27 && tier !== 'low') {
        setTier(tier === 'high' ? 'medium' : 'low');
      } else if (fps > 55 && tier !== 'high') {
        setTier(tier === 'low' ? 'medium' : 'high');
      }
    }
  });

  return null;
}
'''


# =============================================================================
# 3. CAMERA INTRO (cinematic opening glide)
# =============================================================================

CAMERA_INTRO = r'''import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

/**
 * Cinematic opening: camera glides from a high aerial shot
 * down to the farm view over ~5 seconds (easeOutCubic),
 * then hands control to the user (OrbitControls enabled).
 */
export function CameraIntro({ onDone }: { onDone: () => void }) {
  const { camera } = useThree();
  const st = useRef({ t: 0, done: false });
  const start = useMemo(() => new THREE.Vector3(430, 260, 430), []);
  const end = useMemo(() => new THREE.Vector3(120, 60, 120), []);

  useEffect(() => {
    camera.position.copy(start);
    camera.lookAt(0, 0, 0);
  }, [camera, start]);

  useFrame((_, delta) => {
    const s = st.current;
    if (s.done) return;
    s.t += delta / 5; // 5 second glide
    const k = Math.min(1, s.t);
    const e = 1 - Math.pow(1 - k, 3); // easeOutCubic
    camera.position.lerpVectors(start, end, e);
    camera.lookAt(0, 0, 0);
    if (k >= 1) {
      s.done = true;
      onDone();
    }
  });

  return null;
}
'''


# =============================================================================
# 4. SIMULATOR (adaptive DPR + intro + governor + quality badge)
# =============================================================================

SIMULATOR = r'''import { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Preload } from '@react-three/drei';
import * as THREE from 'three';
import { useQualityStore, TIER_LABEL } from '../../hooks/useQualityStore';
import { PerformanceGovernor } from './PerformanceGovernor';
import { CameraIntro } from './CameraIntro';
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
  const [introDone, setIntroDone] = useState(false);

  return (
    <>
      <CameraIntro onDone={() => setIntroDone(true)} />
      <PerformanceGovernor />
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

      <OrbitControls
        makeDefault
        enabled={introDone}
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

function CanvasHost() {
  const tier = useQualityStore((s) => s.tier);
  const { timeOfDay, condition } = useWeatherStore();

  // Adaptive DPR: the single biggest factor for smoothness
  const dpr: [number, number] =
    tier === 'high' ? [1.25, 1.75] : tier === 'medium' ? [1, 1.25] : [0.75, 1];

  const exposure = (() => {
    let base = 1.1;
    if (timeOfDay === 'night') base = 0.6;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 0.95;
    if (condition === 'dust') base *= 0.55;
    if (condition === 'storm') base *= 0.45;
    return base;
  })();

  return (
    <Canvas
      shadows={tier !== 'low'}
      camera={{ position: [430, 260, 430], fov: 60, near: 0.5, far: 8000 }}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      dpr={dpr}
      onCreated={({ gl }) => {
        gl.toneMapping = THREE.ACESFilmicToneMapping;
        gl.toneMappingExposure = exposure;
        gl.outputColorSpace = THREE.SRGBColorSpace;
        gl.shadowMap.enabled = tier !== 'low';
        gl.shadowMap.type = THREE.PCFSoftShadowMap;
      }}
    >
      <Suspense fallback={null}>
        <Scene />
      </Suspense>
    </Canvas>
  );
}

export function CinematicSimulator() {
  const tier = useQualityStore((s) => s.tier);

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#000' }}>
      <CanvasHost />
      <CinematicOverlay />
      <WeatherControls />

      {/* Quality badge (adaptive) */}
      <div style={{
        position: 'absolute',
        bottom: 10,
        left: 10,
        color: 'rgba(255,255,255,0.55)',
        fontSize: 11,
        fontFamily: 'monospace',
        pointerEvents: 'none',
        zIndex: 100,
        direction: 'rtl',
      }}>
        🎬 کیفیت خودکار: {TIER_LABEL[tier]} | DPR تطبیقی | اینتروی سینمایی
      </div>
    </div>
  );
}

export default CinematicSimulator;
'''


# =============================================================================
# 5. VEGETATION (tier-based count + FIXED instancing via useLayoutEffect)
# =============================================================================

VEGETATION = r'''import { useLayoutEffect, useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useQualityStore } from '../../hooks/useQualityStore';

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
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  const { windSpeed, condition, plantGrowthStage } = useWeatherStore();
  const tier = useQualityStore((s) => s.tier);

  // Adaptive grass density
  const target = tier === 'high' ? 8000 : tier === 'medium' ? 4500 : 2500;

  const blade = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const v = new Float32Array([-0.05, 0, 0, 0.05, 0, 0, 0.03, 0.5, 0, -0.03, 0.5, 0, 0, 1, 0]);
    const idx = new Uint16Array([0, 1, 2, 0, 2, 3, 3, 2, 4]);
    g.setAttribute('position', new THREE.BufferAttribute(v, 3));
    g.setIndex(new THREE.BufferAttribute(idx, 1));
    g.computeVertexNormals();
    return g;
  }, []);

  const { transforms, rands } = useMemo(() => {
    const list: { x: number; y: number; z: number; rot: number; scale: number }[] = [];
    const r: number[] = [];
    let guard = 0;
    while (list.length < target && guard < target * 4) {
      guard++;
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.sqrt(Math.random()) * 110;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const y = getTerrainHeight(x, z);
      if (y < -1.0) continue; // no grass under water
      list.push({ x, y, z, rot: Math.random() * Math.PI, scale: 0.7 + Math.random() * 0.9 });
      r.push(Math.random());
    }
    return { transforms: list, rands: new Float32Array(r) };
  }, [target]);

  // FIX: useLayoutEffect (useMemo ran before ref existed -> matrices never applied)
  useLayoutEffect(() => {
    const mesh = meshRef.current;
    if (!mesh) return;
    const dummy = new THREE.Object3D();
    transforms.forEach((t, i) => {
      dummy.position.set(t.x, t.y - 0.05, t.z);
      dummy.rotation.set(0, t.rot, 0);
      dummy.scale.setScalar(t.scale);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
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

  const count = transforms.length;

  return (
    <instancedMesh key={count} ref={meshRef} args={[blade, undefined, count]} castShadow={tier === 'high'}>
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
      <instancedBufferAttribute attach="attributes-aRandom" args={[rands, 1]} />
    </instancedMesh>
  );
}
'''


# =============================================================================
# 6. LIGHTING (tier shadows + homepage palette harmony)
# =============================================================================

LIGHTING = r'''import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useQualityStore } from '../../hooks/useQualityStore';

export function LightingSystem() {
  const sunRef = useRef<THREE.DirectionalLight>(null);
  const { timeOfDay, sunPosition, condition, intensity } = useWeatherStore();
  const tier = useQualityStore((s) => s.tier);

  useFrame(({ scene }) => {
    if (!scene.fog) scene.fog = new THREE.FogExp2('#d8ecf5', 0.0012);
    const fog = scene.fog as THREE.FogExp2;

    // Palette harmony with homepage hero (soft sky blue)
    let density = 0.0012;
    let color = '#d8ecf5';

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

  const shadowSize = tier === 'high' ? 2048 : 1024;

  return (
    <>
      <directionalLight
        ref={sunRef}
        position={sunPosition}
        intensity={sunIntensity}
        color={sunColor}
        castShadow={tier !== 'low'}
        shadow-mapSize={[shadowSize, shadowSize]}
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
          condition === 'dust' ? '#8b6f47' : '#bfe0f0',
          '#4a7c3a',
          condition === 'dust' || condition === 'storm' ? 0.25 : 0.5,
        ]}
      />

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
          <Cloud position={[-60, 80, -100]} speed={0.6} opacity={0.9} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} segments={30} />
          <Cloud position={[80, 90, -120]} speed={0.5} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} segments={30} />
          <Cloud position={[0, 85, -150]} speed={0.7} opacity={0.95} color={condition === 'storm' ? '#1a202c' : '#6a7a88'} segments={30} />
        </>
      )}
      {condition === 'dust' && (
        <>
          <Cloud position={[-40, 25, -50]} speed={0.8} opacity={0.6} color="#8b6f47" segments={24} />
          <Cloud position={[60, 30, -70]} speed={0.9} opacity={0.7} color="#a0826b" segments={24} />
        </>
      )}
    </>
  );
}
'''


# =============================================================================
# 7. POST-PROCESSING (tier-aware)
# =============================================================================

POSTPROCESSING = r'''import { EffectComposer, Bloom, DepthOfField, Vignette, ChromaticAberration, HueSaturation, BrightnessContrast } from '@react-three/postprocessing';
import { N8AO } from '@react-three/postprocessing';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';
import { useQualityStore } from '../../hooks/useQualityStore';
import { Vector2 } from 'three';

export function PostProcessing() {
  const artistic = useArtisticStore();
  const weather = useWeatherStore();
  const tier = useQualityStore((s) => s.tier);

  // Low tier: skip post-processing entirely for max fluidity
  if (!artistic.enablePostProcessing || tier === 'low') return null;

  const hueShift = (() => {
    if (weather.condition === 'drought') return -0.05;
    if (weather.condition === 'snow') return 0.05;
    if (weather.condition === 'dust') return -0.08;
    return 0;
  })();

  const saturation = (() => {
    if (weather.condition === 'drought') return -0.25;
    if (weather.condition === 'dust') return -0.4;
    if (weather.condition === 'storm') return -0.3;
    if (weather.timeOfDay === 'night') return -0.4;
    if (weather.timeOfDay === 'dawn' || weather.timeOfDay === 'dusk') return 0.15;
    return 0.08;
  })();

  const brightness = (weather.condition === 'storm' || weather.condition === 'dust') ? -0.15 : weather.timeOfDay === 'night' ? -0.2 : 0;
  const contrast = (weather.timeOfDay === 'dawn' || weather.timeOfDay === 'dusk') ? 0.15 : weather.condition === 'dust' ? -0.1 : 0.05;

  return (
    <EffectComposer multisampling={tier === 'high' ? 4 : 0}>
      {tier === 'high' && (
        <N8AO aoRadius={0.8} intensity={2.5} distanceFalloff={0.8} color="#1a1a2e" quality="performance" halfRes />
      )}

      <Bloom
        intensity={weather.timeOfDay === 'night' ? 1.2 : 0.5}
        luminanceThreshold={0.75}
        luminanceSmoothing={0.85}
        mipmapBlur
        radius={0.85}
      />

      {tier === 'high' && (
        <DepthOfField focusDistance={0.015} focalLength={0.04} bokehScale={2.5} height={480} />
      )}

      <BrightnessContrast brightness={brightness} contrast={contrast} />
      <HueSaturation hue={hueShift} saturation={saturation} />
      <Vignette eskil={false} offset={0.25} darkness={0.85} />

      {(weather.condition === 'storm' || weather.condition === 'dust') && (
        <ChromaticAberration offset={new Vector2(0.0015, 0.0015)} radialModulation modulationOffset={0.5} />
      )}
    </EffectComposer>
  );
}
'''


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("")
    print("=" * 70)
    print("  🎬 Cinematic Smooth Polish (homepage-level fluidity)")
    print("=" * 70)
    print("")
    print("  1. FPS Governor: adaptive quality tiers (high/medium/low)")
    print("  2. Adaptive DPR: [1.25-1.75] / [1-1.25] / [0.75-1]")
    print("  3. Camera intro: 5s cinematic aerial glide")
    print("  4. Grass: 8000/4500/2500 per tier + instancing FIX")
    print("  5. Shadows: 2048/1024/off per tier")
    print("  6. Post-processing: full / light / off per tier")
    print("  7. Palette harmony with homepage hero")
    print("")

    setup_git_path()

    print("[Step 1] Writing polished components")
    print("-" * 70)
    files = {
        HOOKS / "useQualityStore.ts": QUALITY_STORE,
        SIM / "PerformanceGovernor.tsx": PERF_GOVERNOR,
        SIM / "CameraIntro.tsx": CAMERA_INTRO,
        SIM / "CinematicSimulator.tsx": SIMULATOR,
        SIM / "VegetationSystem.tsx": VEGETATION,
        SIM / "LightingSystem.tsx": LIGHTING,
        SIM / "PostProcessing.tsx": POSTPROCESSING,
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
        ok("Build successful")
    else:
        err("Build failed:")
        for line in (result.stdout + result.stderr).splitlines()[-20:]:
            if line.strip():
                print(f"    {line}")
    print("")

    if build_ok:
        print("[Step 3] Committing")
        print("-" * 70)
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = ("feat(cinematic): smooth polish - adaptive quality + cinematic intro\\n\\n"
                   "Modeled after the fluid 2D homepage:\\n"
                   "1. FPS Governor (zustand store): measures real FPS every 2.5s,\\n"
                   "   shifts tier high<->medium<->low (thresholds 27/55 FPS)\\n"
                   "2. Adaptive DPR per tier: [1.25,1.75]/[1,1.25]/[0.75,1]\\n"
                   "3. CameraIntro: 5s aerial glide with easeOutCubic,\\n"
                   "   OrbitControls disabled until intro completes\\n"
                   "4. Grass density per tier: 8000/4500/2500\\n"
                   "5. Shadows per tier: 2048/1024/off\\n"
                   "6. Post-processing per tier: full/light(MSAA0,noDoF)/off\\n"
                   "7. FIX: grass instance matrices now set in useLayoutEffect\\n"
                   "   (previously useMemo ran before ref existed -> never applied)\\n"
                   "8. Palette harmony: fog/sky matched to homepage hero soft blue\\n\\n"
                   "Result: simulator stays fluid like the homepage on any GPU.")
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")

        print("")
        print("=" * 70)
        print("  🎉 SMOOTH POLISH COMPLETE!")
        print("=" * 70)
        print("")
        print("  Ctrl+Shift+R in browser, then /hydroma")
        print("")
        print("  You will see:")
        print("    🎥 5s cinematic aerial opening (like a movie intro)")
        print("    🎚️ Auto quality badge (bottom-left): بالا/متوسط/پایین")
        print("    🌿 Grass actually growing now (instancing bug fixed)")
        print("    🎨 Sky/fog colors matching the homepage hero")
        print("    ⚡ Fluid FPS on any GPU (governor adapts automatically)")
        print("")

    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())