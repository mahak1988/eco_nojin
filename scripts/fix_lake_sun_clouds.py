#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lake/Sun/Clouds rework per user feedback
=========================================
1. Remove GodRays entirely (user request)
2. Organic circular lake (no more square plane)
3. Continuous sandy beach ring hugging terrain (no white rectangles)
4. Moving clouds (drift with wind, fair-weather clouds in clear sky)
5. Moving sun: full day cycle (180s) with dynamic light color/intensity
6. SunCycle toggle replaces GodRays button in control panel
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
# 1. CUSTOM WATER - organic circular lake (no square edges)
# =============================================================================

CUSTOM_WATER = r'''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface Props {
  position?: [number, number, number];
  radius?: number;
  color?: string;
  waveHeight?: number;
  waveSpeed?: number;
  segments?: number;
}

/**
 * Organic lake: circular geometry + noise-wobbled shoreline alpha.
 * No more square water plane!
 */
export function CustomWater({
  position = [0, 0, 0],
  radius = 55,
  color = '#2a5a8a',
  waveHeight = 0.15,
  waveSpeed = 0.5,
  segments = 96,
}: Props) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uColor: { value: new THREE.Color(color) },
    uWaveHeight: { value: waveHeight },
    uWaveSpeed: { value: waveSpeed },
  }), [color, waveHeight, waveSpeed]);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
  });

  return (
    <mesh position={position} rotation={[-Math.PI / 2, 0, 0]}>
      <circleGeometry args={[radius, segments]} />
      <shaderMaterial
        ref={materialRef}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        side={THREE.DoubleSide}
        vertexShader={`
          uniform float uTime;
          uniform float uWaveHeight;
          uniform float uWaveSpeed;
          varying vec2 vUv;
          varying float vWave;
          void main() {
            vUv = uv;
            vec3 p = position;
            float t = uTime * uWaveSpeed;
            float w1 = sin(p.x * 0.25 + t * 1.6) * cos(p.y * 0.2 + t * 1.1);
            float w2 = sin((p.x + p.y) * 0.5 + t * 2.2) * 0.4;
            p.z = (w1 + w2) * uWaveHeight;
            vWave = p.z;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
          }
        `}
        fragmentShader={`
          uniform vec3 uColor;
          uniform float uTime;
          varying vec2 vUv;
          varying float vWave;

          void main() {
            // radial distance from lake center (0..1 at rim)
            float r = length(vUv - 0.5) * 2.0;

            // wobble the shoreline so it looks natural, not circular-perfect
            float wob = sin(vUv.x * 34.0 + uTime * 0.4) * 0.03
                      + cos(vUv.y * 29.0 - uTime * 0.3) * 0.03;
            float shore = smoothstep(1.0 + wob, 0.86 + wob, r);
            if (shore < 0.01) discard;

            // depth gradient: deep center -> shallow rim
            vec3 deep = uColor * 0.55;
            vec3 shallow = uColor * 1.35;
            vec3 col = mix(shallow, deep, smoothstep(0.3, 0.9, r) * -1.0 + 1.0);
            col = mix(deep, shallow, 1.0 - smoothstep(0.2, 0.95, r));

            // moving highlights
            float spec = pow(max(sin(vUv.x * 60.0 + uTime * 1.4) * sin(vUv.y * 55.0 - uTime * 1.1), 0.0), 6.0);
            col += vec3(0.9, 0.95, 1.0) * spec * 0.25;

            // foam near shore
            float foam = smoothstep(0.9, 0.99, r + wob) * 0.6;
            col = mix(col, vec3(0.92, 0.97, 1.0), foam);

            gl_FragColor = vec4(col, 0.9 * shore);
          }
        `}
      />
    </mesh>
  );
}

export default CustomWater;
'''


# =============================================================================
# 2. WATER SYSTEM
# =============================================================================

WATER_SYSTEM = r'''import { CustomWater } from './CustomWater';
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
    <CustomWater
      position={[0, LAKE_LEVEL, 0]}
      radius={55}
      color={waterColor}
      waveHeight={waveHeight}
      waveSpeed={condition === 'storm' ? 1.2 : 0.5}
    />
  );
}
'''


# =============================================================================
# 3. COASTLINE - continuous sandy beach hugging terrain
# =============================================================================

COASTLINE = r'''import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

/**
 * Continuous beach: 56 overlapping sand quads hugging the terrain,
 * oriented tangentially (no more scattered white rectangles).
 */
export function Coastline() {
  const patches = useMemo(() => {
    const list: { x: number; z: number; y: number; yaw: number; s: number }[] = [];
    const N = 56;
    for (let i = 0; i < N; i++) {
      const a = (i / N) * Math.PI * 2;
      const r = 58 + Math.sin(i * 2.7) * 3;
      const x = Math.cos(a) * r;
      const z = Math.sin(a) * r;
      const y = getTerrainHeight(x, z) + 0.06;
      list.push({ x, z, y, yaw: -a + Math.PI / 2, s: 0.9 + Math.sin(i * 1.3) * 0.15 });
    }
    return list;
  }, []);

  return (
    <group>
      {patches.map((p, i) => (
        <group key={i} position={[p.x, p.y, p.z]} rotation={[0, p.yaw, 0]} scale={p.s}>
          <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
            <planeGeometry args={[11, 9]} />
            <meshStandardMaterial color="#e6d3a3" roughness={0.95} />
          </mesh>
        </group>
      ))}
    </group>
  );
}
'''


# =============================================================================
# 4. LIGHTING - moving sun (day cycle) + drifting clouds
# =============================================================================

LIGHTING = r'''import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore, TimeOfDay } from '../../hooks/useWeatherStore';
import { useQualityStore } from '../../hooks/useQualityStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';

/**
 * Celestial system:
 *  - Moving sun: full day cycle (180s) when "حرکت خورشید" is ON
 *  - Drifting clouds: cloud group moves with wind (visible even on clear days)
 *  - Real sunshine: strong warm directional light with soft shadows at day
 */
export function LightingSystem() {
  const { timeOfDay, sunPosition, condition, intensity, windSpeed } = useWeatherStore();
  const tier = useQualityStore((s) => s.tier);
  const enableSunCycle = useArtisticStore((s) => s.enableSunCycle);

  const cycle = useRef(0.30); // start at morning
  const acc = useRef(0);
  const [liveSun, setLiveSun] = useState<[number, number, number]>(sunPosition);
  const [livePhase, setLivePhase] = useState<TimeOfDay>(timeOfDay);
  const cloudsRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    // --- Clouds ALWAYS drift with the wind ---
    if (cloudsRef.current) {
      cloudsRef.current.position.x += delta * (2 + windSpeed * 0.4);
      if (cloudsRef.current.position.x > 260) cloudsRef.current.position.x = -260;
    }

    // --- Sun cycle ---
    if (!enableSunCycle) return;
    cycle.current = (cycle.current + delta / 180) % 1; // 180s full day
    acc.current += delta;
    if (acc.current < 0.15) return; // throttle React updates
    acc.current = 0;

    const t = cycle.current;
    const el = Math.sin(t * Math.PI * 2);       // elevation -1..1
    const az = t * Math.PI * 2;                 // azimuth
    const R = 400;
    const horiz = Math.sqrt(Math.max(0.05, 1 - el * el));
    setLiveSun([Math.cos(az) * horiz * R, el * R, Math.sin(az) * horiz * R * 0.5]);

    let ph: TimeOfDay;
    if (el > 0.35) ph = 'day';
    else if (el > 0) ph = Math.cos(az) > 0 ? 'dawn' : 'dusk';
    else ph = 'night';
    setLivePhase(ph);
  });

  const phase: TimeOfDay = enableSunCycle ? livePhase : timeOfDay;
  const sun = enableSunCycle ? liveSun : sunPosition;

  // Fog
  useFrame(({ scene }) => {
    if (!scene.fog) scene.fog = new THREE.FogExp2('#d8ecf5', 0.0012);
    const fog = scene.fog as THREE.FogExp2;
    let density = 0.0012;
    let color = '#d8ecf5';
    if (condition === 'dust')       { density = 0.016 + intensity * 0.015; color = '#a08055'; }
    else if (condition === 'storm') { density = 0.012 + intensity * 0.012; color = '#5a6675'; }
    else if (condition === 'rain')  { density = 0.005; color = '#93a5b5'; }
    else if (condition === 'snow')  { density = 0.005; color = '#dfe5ee'; }
    else if (condition === 'drought'){ density = 0.0025; color = '#d8c49a'; }
    else if (phase === 'night')     { density = 0.0015; color = '#0a1520'; }
    else if (phase === 'dawn')      { density = 0.002; color = '#ffd9b0'; }
    else if (phase === 'dusk')      { density = 0.002; color = '#ffc9a0'; }
    fog.density += (density - fog.density) * 0.06;
    fog.color.lerp(new THREE.Color(color), 0.06);
  });

  // --- Sunshine intensity & color (تابش خورشید) ---
  const sunIntensity = (() => {
    let base = 2.6; // strong daylight sunshine
    if (phase === 'night') base = 0.15;
    else if (phase === 'dawn' || phase === 'dusk') base = 1.2;
    if (condition === 'dust') base *= 0.25;
    if (condition === 'storm') base *= 0.18;
    if (condition === 'rain') base *= 0.5;
    if (condition === 'snow') base *= 0.7;
    return base;
  })();

  const sunColor = (() => {
    if (condition === 'dust') return '#d4935a';
    if (condition === 'storm') return '#8a9aa8';
    if (phase === 'dawn') return '#ffb347';
    if (phase === 'dusk') return '#ff6b6b';
    if (phase === 'night') return '#4a6fa5';
    return '#fff3d6'; // warm sunshine
  })();

  const shadowSize = tier === 'high' ? 2048 : 1024;

  return (
    <>
      <directionalLight
        position={sun}
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
      <ambientLight intensity={phase === 'night' ? 0.2 : condition === 'dust' || condition === 'storm' ? 0.25 : 0.45} color={sunColor} />
      <hemisphereLight
        args={[
          condition === 'dust' ? '#8b6f47' : '#bfe0f0',
          '#4a7c3a',
          condition === 'dust' || condition === 'storm' ? 0.25 : 0.5,
        ]}
      />

      {phase !== 'night' && (
        <Sky
          distance={3500}
          sunPosition={sun}
          mieCoefficient={condition === 'dust' ? 0.12 : condition === 'storm' ? 0.08 : 0.005}
          rayleigh={condition === 'dust' ? 6 : condition === 'storm' ? 4 : 1.5}
          turbidity={condition === 'dust' ? 18 : condition === 'storm' ? 12 : 6}
        />
      )}

      {phase === 'night' && <Stars radius={800} depth={100} count={8000} factor={6} saturation={0.2} fade speed={0.5} />}

      {/* --- MOVING CLOUDS (حرکت ابرها) --- */}
      <group ref={cloudsRef}>
        {/* Fair-weather clouds on clear days */}
        {(condition === 'clear' || condition === 'drought') && phase !== 'night' && (
          <>
            <Cloud position={[-90, 95, -140]} speed={0.4} opacity={0.5} color="#ffffff" segments={24} />
            <Cloud position={[30, 105, -170]} speed={0.3} opacity={0.45} color="#ffffff" segments={24} />
            <Cloud position={[130, 90, -100]} speed={0.5} opacity={0.5} color="#ffffff" segments={24} />
          </>
        )}
        {(condition === 'storm' || condition === 'rain') && (
          <>
            <Cloud position={[-60, 80, -100]} speed={0.8} opacity={0.9} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} segments={30} />
            <Cloud position={[80, 90, -120]} speed={0.7} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} segments={30} />
            <Cloud position={[0, 85, -150]} speed={0.9} opacity={0.95} color={condition === 'storm' ? '#1a202c' : '#6a7a88'} segments={30} />
          </>
        )}
        {condition === 'dust' && (
          <>
            <Cloud position={[-40, 25, -50]} speed={1.2} opacity={0.6} color="#8b6f47" segments={24} />
            <Cloud position={[60, 30, -70]} speed={1.4} opacity={0.7} color="#a0826b" segments={24} />
          </>
        )}
        {condition === 'snow' && (
          <Cloud position={[0, 90, -130]} speed={0.5} opacity={0.7} color="#dfe5ee" segments={24} />
        )}
      </group>
    </>
  );
}
'''


# =============================================================================
# 5. ARTISTIC STORE (add enableSunCycle, godRays default OFF)
# =============================================================================

ARTISTIC_STORE = r'''import { create } from 'zustand';

export type Season = 'spring' | 'summer' | 'autumn' | 'winter';

export interface ArtisticState {
  season: Season;
  enableAurora: boolean;
  enableRainbow: boolean;
  enableFireflies: boolean;
  enableBirds: boolean;
  enableButterflies: boolean;
  enableGodRays: boolean;      // deprecated - kept false, no longer rendered
  enableSunCycle: boolean;     // NEW: moving sun day cycle
  enableCinematicCamera: boolean;
  enableLetterbox: boolean;
  enableFilmGrain: boolean;
  enableLensFlare: boolean;
  timeScale: number;
  enableInsects: boolean;
  enableDomesticAnimals: boolean;
  enablePoultry: boolean;
  enableFlood: boolean;
  enableIrrigation: boolean;
  enableWell: boolean;
  enableRiver: boolean;
  enableCoastline: boolean;
  enableWatershed: boolean;
  enablePlowing: boolean;

  setSeason: (s: Season) => void;
  toggle: (key: string) => void;
  setTimeScale: (t: number) => void;
}

export const useArtisticStore = create<ArtisticState>((set) => ({
  season: 'summer',
  enableAurora: false,
  enableRainbow: false,
  enableFireflies: false,
  enableBirds: true,
  enableButterflies: true,
  enableGodRays: false,
  enableSunCycle: true,
  enableCinematicCamera: false,
  enableLetterbox: true,
  enableFilmGrain: true,
  enableLensFlare: false,
  timeScale: 1,
  enableInsects: true,
  enableDomesticAnimals: true,
  enablePoultry: true,
  enableFlood: false,
  enableIrrigation: true,
  enableWell: true,
  enableRiver: true,
  enableCoastline: true,
  enableWatershed: true,
  enablePlowing: true,

  setSeason: (season) => set({ season }),
  toggle: (key) => set((s) => ({ [key]: !(s as any)[key] })),
  setTimeScale: (timeScale) => set({ timeScale }),
}));
'''


# =============================================================================
# 6. SIMULATOR (GodRays removed)
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

      {/* NOTE: GodRays removed per user request - replaced by
          moving sun + drifting clouds + real sunshine in LightingSystem */}

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
      <div style={{
        position: 'absolute', bottom: 10, left: 10,
        color: 'rgba(255,255,255,0.55)', fontSize: 11, fontFamily: 'monospace',
        pointerEvents: 'none', zIndex: 100, direction: 'rtl',
      }}>
        🎬 کیفیت خودکار: {TIER_LABEL[tier]} | خورشید متحرک + ابرهای متحرک
      </div>
    </div>
  );
}

export default CinematicSimulator;
'''


# =============================================================================
# 7. WEATHER CONTROLS (sun cycle button replaces god rays)
# =============================================================================

WEATHER_CONTROLS = r'''import { useWeatherStore, WeatherCondition, TimeOfDay } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';
import { Card, Slider, Button, Space, Typography, Row, Col, Divider } from 'antd';
import { useState } from 'react';

const { Text } = Typography;

const conditions: { value: WeatherCondition; label: string; emoji: string }[] = [
  { value: 'clear', label: 'آفتابی', emoji: '☀️' },
  { value: 'rain', label: 'باران', emoji: '🌧️' },
  { value: 'snow', label: 'برف', emoji: '❄️' },
  { value: 'dust', label: 'ریزگرد', emoji: '🌫️' },
  { value: 'drought', label: 'خشکسالی', emoji: '🏜️' },
  { value: 'storm', label: 'طوفان', emoji: '⛈️' },
];

const times: { value: TimeOfDay; label: string; emoji: string }[] = [
  { value: 'dawn', label: 'طلوع', emoji: '🌅' },
  { value: 'day', label: 'روز', emoji: '☀️' },
  { value: 'dusk', label: 'غروب', emoji: '🌇' },
  { value: 'night', label: 'شب', emoji: '🌙' },
];

const agriculturalFeatures = [
  { key: 'enableInsects', label: 'حشرات', emoji: '🐝' },
  { key: 'enableDomesticAnimals', label: 'دام', emoji: '🐄' },
  { key: 'enablePoultry', label: 'طیور', emoji: '🐔' },
  { key: 'enableFlood', label: 'سیلاب', emoji: '🌊' },
  { key: 'enableIrrigation', label: 'آبیاری', emoji: '💧' },
  { key: 'enableWell', label: 'چاه', emoji: '⛲' },
  { key: 'enableRiver', label: 'رودخانه', emoji: '🏞️' },
  { key: 'enableCoastline', label: 'ساحل', emoji: '🏖️' },
  { key: 'enableWatershed', label: 'آبخیزداری', emoji: '🏗️' },
  { key: 'enablePlowing', label: 'شخم‌زنی', emoji: '🚜' },
];

const artisticEffects = [
  { key: 'enableSunCycle', label: 'حرکت خورشید', emoji: '🌞' },
  { key: 'enableAurora', label: 'شفق قطبی', emoji: '🌌' },
  { key: 'enableRainbow', label: 'رنگین‌کمان', emoji: '🌈' },
  { key: 'enableFireflies', label: 'کرم شب‌تاب', emoji: '✨' },
  { key: 'enableBirds', label: 'پرندگان', emoji: '🦅' },
  { key: 'enableButterflies', label: 'پروانه', emoji: '🦋' },
  { key: 'enableLetterbox', label: 'لترباکس', emoji: '🎬' },
  { key: 'enableFilmGrain', label: 'گرین فیلم', emoji: '📽️' },
];

export function WeatherControls() {
  const store = useWeatherStore();
  const a = useArtisticStore();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Card
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>🎬 کنترل سینمایی</span>
          <Button type="text" size="small" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? '▼' : '▲'}
          </Button>
        </div>
      }
      style={{
        position: 'absolute', top: 20, right: 20, width: 380,
        maxHeight: 'calc(100vh - 40px)', overflowY: 'auto',
        background: 'rgba(20, 20, 30, 0.9)', backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)', color: 'white', zIndex: 1000,
      }}
      styles={{
        header: { borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'white' },
        body: { color: 'white', padding: collapsed ? 0 : 16 },
      }}
    >
      {!collapsed && (
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <Text strong style={{ color: '#aaa' }}>🌤️ آب و هوا</Text>
            <Row gutter={[6, 6]} style={{ marginTop: 6 }}>
              {conditions.map((c) => (
                <Col key={c.value} span={8}>
                  <Button
                    type={store.condition === c.value ? 'primary' : 'default'}
                    onClick={() => store.setCondition(c.value)}
                    block size="small" style={{ fontSize: 13 }}
                  >{c.emoji} {c.label}</Button>
                </Col>
              ))}
            </Row>
          </div>

          <div>
            <Text strong style={{ color: '#aaa' }}>⏰ زمان روز</Text>
            <Row gutter={[6, 6]} style={{ marginTop: 6 }}>
              {times.map((t) => (
                <Col key={t.value} span={6}>
                  <Button
                    type={store.timeOfDay === t.value ? 'primary' : 'default'}
                    onClick={() => store.setTimeOfDay(t.value)}
                    block size="small"
                  >{t.emoji} {t.label}</Button>
                </Col>
              ))}
            </Row>
          </div>

          <div>
            <Text strong style={{ color: '#aaa' }}>💨 باد: {store.windSpeed} km/h</Text>
            <Slider min={0} max={100} value={store.windSpeed}
              onChange={(v) => store.setWind(v, store.windDirection)} />
          </div>

          <div>
            <Text strong style={{ color: '#aaa' }}>🌱 رشد گیاه: {Math.round(store.plantGrowthStage * 100)}%</Text>
            <Slider min={0} max={100} value={store.plantGrowthStage * 100}
              onChange={(v) => store.setPlantGrowth(v / 100)} />
          </div>

          <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />

          <div>
            <Text strong style={{ color: '#feca57', fontSize: 13 }}>🌾 اکوسیستم کشاورزی</Text>
            <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
              {agriculturalFeatures.map(({ key, label, emoji }) => (
                <Col key={key} span={12}>
                  <Button
                    type={(a as any)[key] ? 'primary' : 'default'}
                    onClick={() => a.toggle(key)} block size="small"
                    style={{ textAlign: 'right' }}
                  >{emoji} {label}</Button>
                </Col>
              ))}
            </Row>
          </div>

          <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />

          <div>
            <Text strong style={{ color: '#feca57', fontSize: 13 }}>✨ جلوه‌های هنری</Text>
            <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
              {artisticEffects.map(({ key, label, emoji }) => (
                <Col key={key} span={12}>
                  <Button
                    type={(a as any)[key] ? 'primary' : 'default'}
                    onClick={() => a.toggle(key)} block size="small"
                  >{emoji} {label}</Button>
                </Col>
              ))}
            </Row>
          </div>
        </Space>
      )}
    </Card>
  );
}
'''


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("")
    print("=" * 70)
    print("  🌞 Lake/Sun/Clouds Rework")
    print("=" * 70)
    print("")
    print("  1. GodRays REMOVED (user request)")
    print("  2. Organic circular lake (square plane gone)")
    print("  3. Continuous sandy beach (white rectangles gone)")
    print("  4. Moving clouds (drift with wind, even on clear days)")
    print("  5. Moving sun: 180s day cycle with dynamic light")
    print("  6. 'حرکت خورشید' toggle in panel (replaces god rays)")
    print("")

    setup_git_path()

    print("[Step 1] Writing components")
    print("-" * 70)
    files = {
        SIM / "CustomWater.tsx": CUSTOM_WATER,
        SIM / "WaterSystem.tsx": WATER_SYSTEM,
        SIM / "Coastline.tsx": COASTLINE,
        SIM / "LightingSystem.tsx": LIGHTING,
        SIM / "CinematicSimulator.tsx": SIMULATOR,
        SIM / "WeatherControls.tsx": WEATHER_CONTROLS,
        HOOKS / "useArtisticStore.ts": ARTISTIC_STORE,
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
            msg = ("feat(cinematic): remove god rays, add moving sun & clouds, organic lake\\n\\n"
                   "Per user feedback:\\n"
                   "1. GodRays removed completely\\n"
                   "2. Sun now MOVES: 180s full day cycle (elevation+azimuth),\\n"
                   "   dynamic light color/intensity, dawn/day/dusk/night phases\\n"
                   "3. Clouds now MOVE: cloud group drifts with wind speed;\\n"
                   "   fair-weather white clouds added for clear days\\n"
                   "4. Strong warm sunshine at day (intensity 2.6)\\n"
                   "5. Lake is now organic: circular geometry + noise-wobbled\\n"
                   "   shoreline alpha (square water plane eliminated)\\n"
                   "6. Beach is now 56 overlapping terrain-hugging sand quads\\n"
                   "   oriented tangentially (white rectangles eliminated)\\n"
                   "7. Control panel: 'حرکت خورشید' toggle replaces god rays")
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")

        print("")
        print("=" * 70)
        print("  🎉 COMPLETE!")
        print("=" * 70)
        print("")
        print("  Ctrl+Shift+R → http://localhost:5173/hydroma")
        print("")
        print("  Watch for ~1 minute:")
        print("    🌞 Sun slowly crosses the sky (shadows rotate)")
        print("    ☁️ Clouds drift with the wind")
        print("    💧 Lake has a natural wavy shoreline (no square!)")
        print("    🏖️ Beach forms a continuous sandy ring")
        print("")

    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())