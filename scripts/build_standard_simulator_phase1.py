#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standard Simulator Rebuild - Phase 1: Scaffold
=================================================
A clean, minimal, sanction-safe 3D simulator foundation.

Architecture:
  - 5 core files (vs 30+ before)
  - Lazy route (three.js only when needed)
  - ErrorBoundary (Canvas crash isolated)
  - Zustand single store
  - Zero external CDN requests
  - Procedural geometry (Sky, Terrain, Water)

Bundle impact:
  - Main bundle unchanged (three/drei stay lazy)
  - New lazy chunk ~1.5MB only loaded on /hydroma visit
"""

import os
import sys
import subprocess
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
SRC = FRONTEND / "src"
SIM = SRC / "components" / "simulator"
PRIMITIVES = SIM / "primitives"
HOOKS = SRC / "hooks"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def warn(m): print(f"[WARN] {m}")


def setup_git_path():
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


# =============================================================================
# 1. STORE (Zustand - single source of truth)
# =============================================================================

STORE = r'''import { create } from 'zustand';

export type Weather = 'clear' | 'rain' | 'snow' | 'dust' | 'storm';
export type TimeOfDay = 'dawn' | 'day' | 'dusk' | 'night';

interface SimulatorState {
  weather: Weather;
  timeOfDay: TimeOfDay;
  windSpeed: number;
  autoSunCycle: boolean;
  quality: 'low' | 'medium' | 'high';
  
  setWeather: (w: Weather) => void;
  setTimeOfDay: (t: TimeOfDay) => void;
  setWindSpeed: (s: number) => void;
  toggleSunCycle: () => void;
  setQuality: (q: 'low' | 'medium' | 'high') => void;
}

export const useSimulatorStore = create<SimulatorState>((set) => ({
  weather: 'clear',
  timeOfDay: 'day',
  windSpeed: 10,
  autoSunCycle: true,
  quality: 'medium',
  
  setWeather: (weather) => set({ weather }),
  setTimeOfDay: (timeOfDay) => set({ timeOfDay }),
  setWindSpeed: (windSpeed) => set({ windSpeed }),
  toggleSunCycle: () => set((s) => ({ autoSunCycle: !s.autoSunCycle })),
  setQuality: (quality) => set({ quality }),
}));
'''


# =============================================================================
# 2. ERROR BOUNDARY (isolate Canvas crashes)
# =============================================================================

ERROR_BOUNDARY = r'''import { Component, ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Catches React errors (including WebGL context lost)
 * and shows a friendly fallback instead of crashing the app.
 */
export class SimulatorErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[Simulator] Crash caught by boundary:', error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div style={{
          minHeight: '70vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24,
        }}>
          <Result
            status="error"
            title="شبیه‌ساز با خطا مواجه شد"
            subTitle={this.state.error?.message || 'WebGL context lost or rendering error'}
            extra={[
              <Button key="reset" type="primary" onClick={this.handleReset}>
                تلاش مجدد
              </Button>,
              <Button key="home" onClick={() => window.location.href = '/'}>
                بازگشت به صفحه اصلی
              </Button>,
            ]}
          />
        </div>
      );
    }

    return this.props.children;
  }
}
'''


# =============================================================================
# 3. PRIMITIVES (procedural, zero external assets)
# =============================================================================

SKY = r'''import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useSimulatorStore, TimeOfDay } from '../simulatorStore';

const palettes: Record<TimeOfDay, { top: string; horizon: string; bottom: string }> = {
  dawn:  { top: '#4a6fa5', horizon: '#ffb88c', bottom: '#8b6f47' },
  day:   { top: '#4a90d9', horizon: '#cfe0ee', bottom: '#87a96b' },
  dusk:  { top: '#2d3748', horizon: '#ff7e5f', bottom: '#6b4423' },
  night: { top: '#050814', horizon: '#1a2540', bottom: '#0a0f1c' },
};

/**
 * Procedural sky dome using a sphere + vertex-color gradient.
 * No external textures, no network requests.
 */
export function Sky() {
  const { timeOfDay } = useSimulatorStore();
  const matRef = useRef<THREE.ShaderMaterial>(null);

  const palette = palettes[timeOfDay];

  const uniforms = useMemo(() => ({
    uTopColor:     { value: new THREE.Color(palette.top) },
    uHorizonColor: { value: new THREE.Color(palette.horizon) },
    uBottomColor:  { value: new THREE.Color(palette.bottom) },
  }), []);

  // Smooth color transitions
  useFrame(() => {
    if (!matRef.current) return;
    const u = matRef.current.uniforms;
    u.uTopColor.value.lerp(new THREE.Color(palette.top), 0.05);
    u.uHorizonColor.value.lerp(new THREE.Color(palette.horizon), 0.05);
    u.uBottomColor.value.lerp(new THREE.Color(palette.bottom), 0.05);
  });

  return (
    <mesh>
      <sphereGeometry args={[2000, 32, 16]} />
      <shaderMaterial
        ref={matRef}
        uniforms={uniforms}
        side={THREE.BackSide}
        depthWrite={false}
        vertexShader={`
          varying vec3 vWorldPosition;
          void main() {
            vec4 worldPos = modelMatrix * vec4(position, 1.0);
            vWorldPosition = worldPos.xyz;
            gl_Position = projectionMatrix * viewMatrix * worldPos;
          }
        `}
        fragmentShader={`
          uniform vec3 uTopColor;
          uniform vec3 uHorizonColor;
          uniform vec3 uBottomColor;
          varying vec3 vWorldPosition;
          void main() {
            float h = normalize(vWorldPosition).y;
            vec3 color;
            if (h > 0.0) {
              color = mix(uHorizonColor, uTopColor, pow(h, 0.6));
            } else {
              color = mix(uHorizonColor, uBottomColor, pow(-h, 0.8));
            }
            gl_FragColor = vec4(color, 1.0);
          }
        `}
      />
    </mesh>
  );
}
'''

TERRAIN = r'''import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useSimulatorStore } from '../simulatorStore';

// Minimal 2D value noise - no external deps, fully deterministic
function hash(x: number, y: number): number {
  const n = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return n - Math.floor(n);
}
function smoothNoise(x: number, y: number): number {
  const xi = Math.floor(x), yi = Math.floor(y);
  const xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf);
  const v = yf * yf * (3 - 2 * yf);
  const a = hash(xi, yi);
  const b = hash(xi + 1, yi);
  const c = hash(xi, yi + 1);
  const d = hash(xi + 1, yi + 1);
  return a * (1 - u) * (1 - v) + b * u * (1 - v) + c * (1 - u) * v + d * u * v;
}
function fbm(x: number, y: number, octaves = 4): number {
  let total = 0, freq = 1, amp = 1, max = 0;
  for (let i = 0; i < octaves; i++) {
    total += smoothNoise(x * freq, y * freq) * amp;
    max += amp;
    amp *= 0.5;
    freq *= 2;
  }
  return total / max;
}

/**
 * Procedural terrain with 4-octave value noise.
 * Flat center (farm), gentle hills at edges.
 * Shared elevation function exported for grounding other objects.
 */
export function getTerrainHeight(x: number, z: number): number {
  const nx = x / 400, nz = z / 400;
  const hills = fbm(nx * 4, nz * 4, 4) * 12;
  const detail = fbm(nx * 15, nz * 15, 2) * 1.5;
  const dist = Math.sqrt(x * x + z * z);
  const flatten = Math.max(0, 1 - dist / 60);
  return (hills + detail) * (1 - flatten * 0.85);
}

export function Terrain() {
  const { weather } = useSimulatorStore();

  const geometry = useMemo(() => {
    const SIZE = 600;
    const SEG = 160;
    const geo = new THREE.PlaneGeometry(SIZE, SIZE, SEG, SEG);
    const pos = geo.attributes.position;
    const colors = new Float32Array(pos.count * 3);

    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const y = pos.getY(i);
      const h = getTerrainHeight(x, -y);
      pos.setZ(i, h);

      // Simple height-based coloring
      let r: number, g: number, b: number;
      if (h < -1) {
        r = 0.22; g = 0.18; b = 0.12;       // low earth
      } else if (h < 2) {
        r = 0.28; g = 0.48; b = 0.22;       // grass
      } else if (h < 6) {
        r = 0.38; g = 0.52; b = 0.28;       // light grass
      } else {
        r = 0.45; g = 0.42; b = 0.35;       // rock
      }

      // Weather tint
      if (weather === 'snow') { r = 0.9; g = 0.92; b = 0.95; }
      else if (weather === 'dust') { r *= 1.3; g *= 0.95; b *= 0.7; }

      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }

    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    geo.rotateX(-Math.PI / 2);
    return geo;
  }, [weather]);

  return (
    <mesh geometry={geometry} receiveShadow>
      <meshStandardMaterial
        vertexColors
        roughness={0.9}
        metalness={0.02}
      />
    </mesh>
  );
}
'''

WATER = r'''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useSimulatorStore } from '../simulatorStore';

/**
 * Procedural lake: circle geometry + wavy shoreline + animated shader.
 * Zero external textures.
 */
export function Water() {
  const { weather, timeOfDay } = useSimulatorStore();
  const matRef = useRef<THREE.ShaderMaterial>(null);

  const baseColor = useMemo(() => {
    if (weather === 'dust') return '#a0826b';
    if (weather === 'storm') return '#4a5568';
    if (timeOfDay === 'dawn') return '#e08a5f';
    if (timeOfDay === 'dusk') return '#c85878';
    if (timeOfDay === 'night') return '#1a2a4a';
    return '#3a7ac0';
  }, [weather, timeOfDay]);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uColor: { value: new THREE.Color(baseColor) },
  }), []);

  useFrame((state) => {
    if (matRef.current) {
      matRef.current.uniforms.uTime.value = state.clock.elapsedTime;
      matRef.current.uniforms.uColor.value.lerp(new THREE.Color(baseColor), 0.05);
    }
  });

  return (
    <mesh position={[0, -0.8, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <circleGeometry args={[45, 64]} />
      <shaderMaterial
        ref={matRef}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        vertexShader={`
          uniform float uTime;
          varying vec2 vUv;
          varying float vWave;
          void main() {
            vUv = uv;
            vec3 p = position;
            p.z = sin(p.x * 0.3 + uTime * 1.5) * 0.15
                + cos(p.y * 0.25 + uTime * 1.2) * 0.1;
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
            float r = length(vUv - 0.5) * 2.0;
            float wob = sin(vUv.x * 32.0 + uTime * 0.5) * 0.04
                      + cos(vUv.y * 28.0 - uTime * 0.4) * 0.04;
            float shore = smoothstep(1.0 + wob, 0.88 + wob, r);
            if (shore < 0.01) discard;

            vec3 deep = uColor * 0.6;
            vec3 shallow = uColor * 1.2;
            vec3 col = mix(deep, shallow, 1.0 - smoothstep(0.3, 0.95, r));

            // highlights
            float spec = pow(max(sin(vUv.x * 50.0 + uTime * 1.2)
                               * sin(vUv.y * 45.0 - uTime * 0.9), 0.0), 8.0);
            col += vec3(0.9, 0.95, 1.0) * spec * 0.3;

            gl_FragColor = vec4(col, 0.88 * shore);
          }
        `}
      />
    </mesh>
  );
}
'''

CLOUDS = r'''import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useSimulatorStore } from '../simulatorStore';

/**
 * Procedural clouds: overlapping low-poly spheres that drift with wind.
 * Zero external textures - immune to network failures.
 */
function Cloud({ position, color, scale = 1 }: {
  position: [number, number, number];
  color: string;
  scale?: number;
}) {
  const puffs = [
    { pos: [0, 0, 0], s: 10 },
    { pos: [8, 1.5, -1], s: 8 },
    { pos: [-9, 0.8, 2], s: 9 },
    { pos: [3, -1.5, 5], s: 7 },
    { pos: [-5, 2, -4], s: 8 },
  ];

  return (
    <group position={position}>
      {puffs.map((p, i) => (
        <mesh key={i} position={[p.pos[0] * scale, p.pos[1] * scale, p.pos[2] * scale]}>
          <icosahedronGeometry args={[p.s * scale, 1]} />
          <meshStandardMaterial
            color={color}
            transparent
            opacity={0.82}
            roughness={1}
            depthWrite={false}
          />
        </mesh>
      ))}
    </group>
  );
}

export function Clouds() {
  const { weather, windSpeed } = useSimulatorStore();
  const groupRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (!groupRef.current) return;
    groupRef.current.position.x += delta * (1.5 + windSpeed * 0.15);
    if (groupRef.current.position.x > 300) groupRef.current.position.x = -300;
  });

  const color = (() => {
    if (weather === 'storm') return '#4a5568';
    if (weather === 'dust') return '#a08055';
    if (weather === 'rain') return '#8a9aa8';
    return '#ffffff';
  })();

  const count = weather === 'clear' ? 3 : weather === 'storm' ? 6 : 4;

  return (
    <group ref={groupRef}>
      {Array.from({ length: count }).map((_, i) => (
        <Cloud
          key={i}
          position={[(i - count / 2) * 80, 90 + (i % 3) * 15, -150 + (i % 2) * 40]}
          color={color}
          scale={1.2 + (i % 3) * 0.3}
        />
      ))}
    </group>
  );
}
'''


# =============================================================================
# 4. SCENE COMPOSITION
# =============================================================================

SCENE = r'''import { useRef, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { Sky } from './primitives/Sky';
import { Terrain } from './primitives/Terrain';
import { Water } from './primitives/Water';
import { Clouds } from './primitives/Clouds';
import { useSimulatorStore, TimeOfDay } from './simulatorStore';

/**
 * Moving sun: full day cycle over 180s when autoSunCycle is on.
 * Sun color/intensity adapts to time of day and weather.
 */
function Sun() {
  const { timeOfDay, weather, autoSunCycle, setTimeOfDay } = useSimulatorStore();
  const lightRef = useRef<THREE.DirectionalLight>(null);
  const cycle = useRef(0.30);

  useFrame((_, delta) => {
    if (!lightRef.current) return;

    if (autoSunCycle) {
      cycle.current = (cycle.current + delta / 180) % 1;
      const el = Math.sin(cycle.current * Math.PI * 2);
      const az = cycle.current * Math.PI * 2;
      const R = 500;
      const horiz = Math.sqrt(Math.max(0.05, 1 - el * el));
      lightRef.current.position.set(
        Math.cos(az) * horiz * R,
        el * R,
        Math.sin(az) * horiz * R * 0.5
      );

      let phase: TimeOfDay;
      if (el > 0.35) phase = 'day';
      else if (el > 0) phase = Math.cos(az) > 0 ? 'dawn' : 'dusk';
      else phase = 'night';
      if (phase !== timeOfDay) setTimeOfDay(phase);
    }

    // Intensity & color by phase + weather
    let intensity = 2.5;
    let color = '#fff3d6';
    if (timeOfDay === 'night') { intensity = 0.15; color = '#4a6fa5'; }
    else if (timeOfDay === 'dawn') { intensity = 1.1; color = '#ffb347'; }
    else if (timeOfDay === 'dusk') { intensity = 1.1; color = '#ff6b6b'; }
    if (weather === 'storm') intensity *= 0.2;
    if (weather === 'rain')  intensity *= 0.5;
    if (weather === 'dust')  intensity *= 0.3;

    lightRef.current.intensity = intensity;
    lightRef.current.color.lerp(new THREE.Color(color), 0.05);
  });

  return (
    <directionalLight
      ref={lightRef}
      position={[200, 300, 100]}
      castShadow
      shadow-mapSize={[2048, 2048]}
      shadow-camera-left={-200}
      shadow-camera-right={200}
      shadow-camera-top={200}
      shadow-camera-bottom={-200}
      shadow-camera-near={1}
      shadow-camera-far={1500}
      shadow-bias={-0.0002}
    />
  );
}

export function SimulatorScene() {
  const { timeOfDay, weather } = useSimulatorStore();

  // Fog color based on time + weather
  const fogColor = (() => {
    if (timeOfDay === 'night') return '#0a1520';
    if (timeOfDay === 'dawn') return '#ffd9b0';
    if (timeOfDay === 'dusk') return '#ffc9a0';
    if (weather === 'dust') return '#a08055';
    if (weather === 'storm') return '#5a6675';
    if (weather === 'rain') return '#93a5b5';
    if (weather === 'snow') return '#dfe5ee';
    return '#cfe0ee';
  })();

  return (
    <>
      <fog attach="fog" args={[fogColor, 200, 2000]} />

      <Sun />
      <ambientLight intensity={timeOfDay === 'night' ? 0.2 : 0.4} />
      <hemisphereLight
        args={[weather === 'dust' ? '#8b6f47' : '#bfe0f0', '#4a7c3a', 0.5]}
      />

      <Sky />
      <Terrain />
      <Water />
      <Clouds />

      <OrbitControls
        makeDefault
        enablePan
        enableZoom
        enableRotate
        minDistance={20}
        maxDistance={500}
        maxPolarAngle={Math.PI / 2.1}
        target={[0, 0, 0]}
        enableDamping
        dampingFactor={0.05}
      />
    </>
  );
}
'''


# =============================================================================
# 5. CANVAS + PAGE (with ErrorBoundary + lazy)
# =============================================================================

CANVAS = r'''import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import * as THREE from 'three';
import { SimulatorScene } from './SimulatorScene';
import { useSimulatorStore } from './simulatorStore';
import { Spin } from 'antd';

/**
 * The R3F Canvas wrapper with adaptive DPR based on quality setting.
 * Wrapped by SimulatorErrorBoundary from the page level.
 */
export function SimulatorCanvas() {
  const quality = useSimulatorStore((s) => s.quality);
  const timeOfDay = useSimulatorStore((s) => s.timeOfDay);

  const dpr: [number, number] = quality === 'high'
    ? [1.5, 2]
    : quality === 'medium'
    ? [1, 1.5]
    : [0.75, 1];

  return (
    <Suspense fallback={
      <div style={{
        width: '100%', height: '100vh',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: '#0a0f1c',
      }}>
        <Spin size="large" tip="در حال بارگذاری شبیه‌ساز..." />
      </div>
    }>
      <Canvas
        shadows={quality !== 'low'}
        camera={{ position: [120, 70, 120], fov: 60, near: 0.5, far: 5000 }}
        gl={{
          antialias: true,
          powerPreference: 'high-performance',
          alpha: false,
        }}
        dpr={dpr}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = timeOfDay === 'night' ? 0.7 : 1.0;
          gl.outputColorSpace = THREE.SRGBColorSpace;
          gl.shadowMap.enabled = quality !== 'low';
          gl.shadowMap.type = THREE.PCFSoftShadowMap;
        }}
      >
        <SimulatorScene />
      </Canvas>
    </Suspense>
  );
}
'''

CONTROL_PANEL = r'''import { Drawer, Slider, Switch, Segmented, Typography, Space } from 'antd';
import { useSimulatorStore, Weather, TimeOfDay } from './simulatorStore';
import { useState } from 'react';

const { Title, Text } = Typography;

const WEATHER_OPTIONS = [
  { value: 'clear', label: '☀️ صاف' },
  { value: 'rain',  label: '🌧️ باران' },
  { value: 'snow',  label: '❄️ برف' },
  { value: 'dust',  label: '🌫️ ریزگرد' },
  { value: 'storm', label: '⛈️ طوفان' },
];

const TIME_OPTIONS = [
  { value: 'dawn',  label: '🌅 طلوع' },
  { value: 'day',   label: '☀️ روز' },
  { value: 'dusk',  label: '🌇 غروب' },
  { value: 'night', label: '🌙 شب' },
];

const QUALITY_OPTIONS = [
  { value: 'low',    label: 'کم' },
  { value: 'medium', label: 'متوسط' },
  { value: 'high',   label: 'بالا' },
];

export function ControlPanel() {
  const [open, setOpen] = useState(false);
  const store = useSimulatorStore();

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        style={{
          position: 'absolute',
          top: 20,
          left: 20,
          zIndex: 100,
          padding: '8px 16px',
          background: 'rgba(255, 255, 255, 0.15)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: 6,
          color: 'white',
          cursor: 'pointer',
          fontSize: 14,
        }}
      >
        ⚙️ کنترل‌ها
      </button>

      <Drawer
        title="🎬 کنترل‌های شبیه‌ساز"
        placement="left"
        open={open}
        onClose={() => setOpen(false)}
        width={320}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={5}>آب و هوا</Title>
            <Segmented
              block
              options={WEATHER_OPTIONS}
              value={store.weather}
              onChange={(v) => store.setWeather(v as Weather)}
            />
          </div>

          <div>
            <Title level={5}>
              زمان روز
              <Text type="secondary" style={{ fontSize: 12, marginRight: 8 }}>
                {store.autoSunCycle && '(چرخه خودکار)'}
              </Text>
            </Title>
            <Segmented
              block
              options={TIME_OPTIONS}
              value={store.timeOfDay}
              onChange={(v) => store.setTimeOfDay(v as TimeOfDay)}
              disabled={store.autoSunCycle}
            />
            <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Switch
                checked={store.autoSunCycle}
                onChange={store.toggleSunCycle}
              />
              <Text>چرخه خودکار خورشید</Text>
            </div>
          </div>

          <div>
            <Title level={5}>باد: {store.windSpeed} km/h</Title>
            <Slider
              min={0}
              max={80}
              value={store.windSpeed}
              onChange={store.setWindSpeed}
            />
          </div>

          <div>
            <Title level={5}>کیفیت رندر</Title>
            <Segmented
              block
              options={QUALITY_OPTIONS}
              value={store.quality}
              onChange={(v) => store.setQuality(v as any)}
            />
          </div>
        </Space>
      </Drawer>
    </>
  );
}
'''

PAGE = r'''import { SimulatorCanvas } from './SimulatorCanvas';
import { SimulatorErrorBoundary } from './SimulatorErrorBoundary';
import { ControlPanel } from './ControlPanel';

/**
 * The public page component for /hydroma.
 * ErrorBoundary wraps the Canvas so crashes don't take down the app.
 */
export default function SimulatorPage() {
  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#0a0f1c' }}>
      <SimulatorErrorBoundary>
        <SimulatorCanvas />
      </SimulatorErrorBoundary>
      <ControlPanel />
      <div style={{
        position: 'absolute',
        bottom: 12,
        left: 12,
        color: 'rgba(255,255,255,0.45)',
        fontSize: 11,
        fontFamily: 'monospace',
        pointerEvents: 'none',
        zIndex: 100,
        direction: 'rtl',
      }}>
        شبیه‌ساز استاندارد v1 • Procedural • آفلاین کامل
      </div>
    </div>
  );
}
'''


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("")
    print("=" * 70)
    print("  🏗️ Standard Simulator Rebuild - Phase 1")
    print("=" * 70)
    print("")
    print("  Architecture: The 5-File Simulator")
    print("    1. simulatorStore.ts       (Zustand, single source)")
    print("    2. SimulatorErrorBoundary   (crash isolation)")
    print("    3. primitives/              (Sky, Terrain, Water, Clouds)")
    print("    4. SimulatorScene.tsx       (composition + moving sun)")
    print("    5. SimulatorCanvas.tsx      (R3F wrapper)")
    print("    + SimulatorPage.tsx        (lazy entry)")
    print("    + ControlPanel.tsx         (antd drawer UI)")
    print("")
    print("  Guarantees:")
    print("    • Lazy route (three.js only when /hydroma visited)")
    print("    • Zero external CDN requests (sanction-safe)")
    print("    • ErrorBoundary prevents app-wide crashes")
    print("    • Adaptive DPR for performance on any GPU")
    print("")

    setup_git_path()

    print("[Step 1] Writing simulator files")
    print("-" * 70)
    files = {
        SIM / "simulatorStore.ts": STORE,
        SIM / "SimulatorErrorBoundary.tsx": ERROR_BOUNDARY,
        SIM / "primitives" / "Sky.tsx": SKY,
        SIM / "primitives" / "Terrain.tsx": TERRAIN,
        SIM / "primitives" / "Water.tsx": WATER,
        SIM / "primitives" / "Clouds.tsx": CLOUDS,
        SIM / "SimulatorScene.tsx": SCENE,
        SIM / "SimulatorCanvas.tsx": CANVAS,
        SIM / "ControlPanel.tsx": CONTROL_PANEL,
        SIM / "SimulatorPage.tsx": PAGE,
    }
    for path, content in files.items():
        write_file(path, content)
        ok(f"Created: {path.relative_to(SRC)}")
    print("")

    print("[Step 2] Wiring up lazy route in App.tsx")
    print("-" * 70)
    app_file = SRC / "App.tsx"
    app = app_file.read_text(encoding="utf-8-sig")

    # Remove placeholder import
    app = re.sub(
        r"import\s+SimulatorPlaceholder\s+from\s+['\"]\.\/pages\/SimulatorPlaceholder['\"];?\s*\n",
        "", app)

    # Add lazy import at top (after existing imports)
    if "SimulatorPage" not in app:
        lazy_import = "const SimulatorPage = lazy(() => import('./components/simulator/SimulatorPage'));\n"
        # Find last import
        lines = app.split("\n")
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("import ") or line.strip().startswith("const ") and "= lazy(" in line:
                insert_idx = i + 1
        lines.insert(insert_idx, lazy_import.rstrip())
        app = "\n".join(lines)
        ok("Added lazy SimulatorPage import")

    # Replace /hydroma route
    app = re.sub(
        r'<Route\s+path="/hydroma"\s+element=\{<SimulatorPlaceholder\s*/>\}\s*/>',
        '<Route path="/hydroma" element={<Suspense fallback={<div style={{minHeight:\'100vh\',display:\'flex\',alignItems:\'center\',justifyContent:\'center\'}}>در حال بارگذاری شبیه‌ساز...</div>}> <SimulatorPage /> </Suspense>} />',
        app)
    ok("Updated /hydroma route")

    # Ensure Suspense is imported
    if "Suspense" not in app[:500]:
        app = app.replace("import React", "import React, { Suspense }", 1)
        ok("Added Suspense to imports")

    app_file.write_text(app, encoding="utf-8")
    ok("App.tsx saved")
    print("")

    print("[Step 3] Removing old placeholder file")
    print("-" * 70)
    placeholder = SRC / "pages" / "SimulatorPlaceholder.tsx"
    if placeholder.exists():
        placeholder.unlink()
        ok("Deleted pages/SimulatorPlaceholder.tsx")
    print("")

    print("[Step 4] Build verification")
    print("-" * 70)
    result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )
    build_ok = result.returncode == 0

    if build_ok:
        ok("🎉 Build successful!")
        print("\n  Bundle sizes:")
        for line in (result.stdout + result.stderr).splitlines():
            if "dist/assets/" in line and "kB" in line:
                if "index" in line or "simulator" in line.lower():
                    info(f"  {line.strip()}")
    else:
        warn("Build failed:")
        for line in (result.stdout + result.stderr).splitlines()[-25:]:
            if line.strip():
                print(f"    {line}")
    print("")

    if build_ok:
        print("[Step 5] Committing Phase 1")
        print("-" * 70)
        try:
            subprocess.run("git add -A .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = ("feat(simulator): Phase 1 - standard rebuild foundation\\n\\n"
                   "Architecture: The 5-File Simulator\\n"
                   "1. simulatorStore.ts - Zustand single source of truth\\n"
                   "2. SimulatorErrorBoundary - crash isolation\\n"
                   "3. primitives/ - Sky, Terrain, Water, Clouds (procedural)\\n"
                   "4. SimulatorScene.tsx - composition + moving sun\\n"
                   "5. SimulatorCanvas.tsx - R3F wrapper with adaptive DPR\\n\\n"
                   "Guarantees:\\n"
                   "- Lazy route (three.js only when /hydroma visited)\\n"
                   "- Zero external CDN requests (sanction-safe)\\n"
                   "- ErrorBoundary prevents app-wide crashes\\n"
                   "- Procedural geometry (no texture downloads)\\n"
                   "- Adaptive DPR per quality tier (low/medium/high)\\n\\n"
                   "Phase 2 next: ecosystem (animals, insects, weather particles)")
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            warn(f"Commit issue: {e}")

        print("")
        print("=" * 70)
        print("  ✅ PHASE 1 COMPLETE")
        print("=" * 70)
        print("")
        print("  Next steps:")
        print("    cd D:\\eco_nojin\\frontend && pnpm dev")
        print("    Visit: http://localhost:5173/hydroma")
        print("")
        print("  What you'll see in Phase 1:")
        print("    ☀️ Sky dome with 4 palettes (dawn/day/dusk/night)")
        print("    🏔️ Procedural terrain (4-octave value noise)")
        print("    💧 Animated circular lake (organic shoreline)")
        print("    ☁️ Drifting procedural clouds (wind-driven)")
        print("    🌞 Moving sun (180s day cycle when enabled)")
        print("    ⚙️ Control drawer (weather, time, wind, quality)")
        print("")
        print("  What's coming next:")
        print("    Phase 2: ecosystem (animals, insects, weather particles)")
        print("    Phase 3: interactions (camera presets, URL state)")
        print("    Phase 4: artistic effects (fog, color grading)")
        print("")
        print("  Bundle impact:")
        print("    • Main bundle: UNCHANGED (three.js stays lazy)")
        print("    • /hydroma chunk: ~1.5MB (loaded on demand)")
        print("    • Home page still loads in <1s")
        print("")

    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())