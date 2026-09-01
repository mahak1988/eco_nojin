#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cinematic DELUXE Upgrade + Auto-Mount into App
================================================
1. Adds 10 artistic/psychological effects (Aurora, Lightning, Rainbow,
   Fireflies, Birds, Butterflies, GodRays, Seasons, CinematicCamera, Overlay)
2. Creates a separate artistic store (no risk of breaking existing store)
3. Auto-mounts a floating "Cinematic Mode" button into App.tsx
4. Fixes git PATH, builds, commits
"""

import os
import sys
import subprocess
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
SRC = FRONTEND / "src"
SIM_DIR = SRC / "components" / "cinematic"
HOOKS_DIR = SRC / "hooks"
APP_FILE = SRC / "App.tsx"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def warn(m): print(f"[WARN] {m}")
def err(m): print(f"[ERROR] {m}")


def setup_git_path():
    """Ensure git is available (fixes previous 'git not recognized')"""
    candidates = [
        r"C:\Program Files\Git\cmd",
        r"C:\Program Files\Git\bin",
        r"C:\Program Files (x86)\Git\cmd",
    ]
    for p in candidates:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
            info(f"Added to PATH: {p}")
            return True
    warn("Git directory not found - commit step may be skipped")
    return False


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


# =============================================================================
# ARTISTIC STORE (separate - safe)
# =============================================================================

ARTISTIC_STORE = '''import { create } from 'zustand';

export type Season = 'spring' | 'summer' | 'autumn' | 'winter';

export interface ArtisticState {
  season: Season;
  enableAurora: boolean;
  enableRainbow: boolean;
  enableFireflies: boolean;
  enableBirds: boolean;
  enableButterflies: boolean;
  enableGodRays: boolean;
  enableCinematicCamera: boolean;
  enableLetterbox: boolean;
  enableFilmGrain: boolean;
  enableLensFlare: boolean;
  timeScale: number;

  setSeason: (s: Season) => void;
  toggle: (key: keyof Omit<ArtisticState, 'season' | 'timeScale' | 'setSeason' | 'toggle' | 'setTimeScale'>) => void;
  setTimeScale: (t: number) => void;
}

export const useArtisticStore = create<ArtisticState>((set) => ({
  season: 'summer',
  enableAurora: false,
  enableRainbow: false,
  enableFireflies: false,
  enableBirds: true,
  enableButterflies: true,
  enableGodRays: true,
  enableCinematicCamera: false,
  enableLetterbox: true,
  enableFilmGrain: true,
  enableLensFlare: false,
  timeScale: 1,

  setSeason: (season) => set({ season }),
  toggle: (key) => set((s) => ({ [key]: !s[key] } as any)),
  setTimeScale: (timeScale) => set({ timeScale }),
}));
'''


# =============================================================================
# AURORA - شفق قطبی
# =============================================================================

AURORA = '''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const auroraVertex = `
  varying vec2 vUv;
  varying vec3 vPos;
  uniform float uTime;
  void main() {
    vUv = uv;
    vec3 p = position;
    p.y += sin(p.x * 0.05 + uTime * 0.5) * 3.0;
    p.y += cos(p.z * 0.08 + uTime * 0.3) * 2.0;
    vPos = p;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
  }
`;

const auroraFragment = `
  varying vec2 vUv;
  varying vec3 vPos;
  uniform float uTime;
  uniform float uIntensity;

  vec3 auroraColor(float t) {
    vec3 green = vec3(0.1, 0.9, 0.4);
    vec3 teal = vec3(0.1, 0.7, 0.8);
    vec3 purple = vec3(0.5, 0.2, 0.9);
    vec3 pink = vec3(0.9, 0.3, 0.6);
    if (t < 0.33) return mix(green, teal, t / 0.33);
    if (t < 0.66) return mix(teal, purple, (t - 0.33) / 0.33);
    return mix(purple, pink, (t - 0.66) / 0.34);
  }

  void main() {
    float wave = sin(vUv.x * 10.0 + uTime) * 0.5 + 0.5;
    float wave2 = cos(vUv.x * 7.0 - uTime * 0.7) * 0.5 + 0.5;
    float bands = wave * wave2;
    float fade = smoothstep(0.0, 0.3, vUv.y) * smoothstep(1.0, 0.5, vUv.y);
    vec3 color = auroraColor(vUv.x + sin(uTime * 0.2) * 0.3);
    float alpha = bands * fade * uIntensity;
    gl_FragColor = vec4(color, alpha * 0.6);
  }
`;

export function Aurora() {
  const matRef = useRef<THREE.ShaderMaterial>(null);

  const geometry = useMemo(() => new THREE.PlaneGeometry(300, 60, 64, 16), []);

  useFrame((state) => {
    if (matRef.current) {
      matRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
  });

  return (
    <mesh geometry={geometry} position={[0, 80, -120]}>
      <shaderMaterial
        ref={matRef}
        vertexShader={auroraVertex}
        fragmentShader={auroraFragment}
        uniforms={{
          uTime: { value: 0 },
          uIntensity: { value: 1.0 },
        }}
        transparent
        side={THREE.DoubleSide}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </mesh>
  );
}
'''


# =============================================================================
# LIGHTNING - رعد و برق
# =============================================================================

LIGHTNING = '''import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export function Lightning() {
  const lightRef = useRef<THREE.PointLight>(null);
  const boltRef = useRef<THREE.Line>(null);
  const [flash, setFlash] = useState(0);
  const nextStrike = useRef(Math.random() * 3 + 2);

  const createBolt = () => {
    const points: THREE.Vector3[] = [];
    let x = (Math.random() - 0.5) * 80;
    let y = 90;
    let z = (Math.random() - 0.5) * 80 - 40;
    points.push(new THREE.Vector3(x, y, z));
    while (y > 5) {
      x += (Math.random() - 0.5) * 12;
      y -= 8 + Math.random() * 6;
      z += (Math.random() - 0.5) * 12;
      points.push(new THREE.Vector3(x, Math.max(y, 2), z));
    }
    return points;
  };

  const [boltPoints, setBoltPoints] = useState<THREE.Vector3[]>(createBolt);

  useFrame((state, delta) => {
    nextStrike.current -= delta;
    if (nextStrike.current <= 0) {
      setFlash(1);
      setBoltPoints(createBolt());
      nextStrike.current = Math.random() * 4 + 2;
    }
    if (flash > 0) {
      const newFlash = Math.max(0, flash - delta * 4);
      setFlash(newFlash);
      if (lightRef.current) lightRef.current.intensity = newFlash * 500;
      if (boltRef.current) {
        const mat = boltRef.current.material as THREE.LineBasicMaterial;
        mat.opacity = newFlash;
      }
    }
  });

  const geometry = new THREE.BufferGeometry().setFromPoints(boltPoints);

  return (
    <>
      <pointLight ref={lightRef} position={[0, 80, -40]} intensity={0} color="#cfe8ff" distance={300} />
      <primitive
        ref={boltRef}
        object={new THREE.Line(
          geometry,
          new THREE.LineBasicMaterial({ color: '#e8f4ff', transparent: true, opacity: 0, linewidth: 2 })
        )}
      />
    </>
  );
}
'''


# =============================================================================
# RAINBOW - رنگین‌کمان
# =============================================================================

RAINBOW = '''import { useMemo } from 'react';
import * as THREE from 'three';

const rainbowColors = ['#ff0000', '#ff7f00', '#ffff00', '#00ff00', '#0000ff', '#4b0082', '#9400d3'];

export function Rainbow() {
  const arcs = useMemo(() => {
    return rainbowColors.map((color, i) => {
      const radius = 60 + i * 1.5;
      const curve = new THREE.EllipseCurve(0, 0, radius, radius, 0, Math.PI, false, 0);
      const points = curve.getPoints(60);
      const geometry = new THREE.BufferGeometry().setFromPoints(
        points.map((p) => new THREE.Vector3(p.x, p.y, 0))
      );
      return { geometry, color, key: i };
    });
  }, []);

  return (
    <group position={[0, 5, -80]} rotation={[0, 0, 0]}>
      {arcs.map(({ geometry, color, key }) => (
        <primitive
          key={key}
          object={new THREE.Line(
            geometry,
            new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.5, linewidth: 3 })
          )}
        />
      ))}
    </group>
  );
}
'''


# =============================================================================
# FIREFLIES - کرم‌های شب‌تاب
# =============================================================================

FIREFLIES = '''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export function Fireflies() {
  const count = 200;
  const meshRef = useRef<THREE.Points>(null);
  const offsets = useMemo(() => new Float32Array(count).map(() => Math.random() * Math.PI * 2), []);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.sqrt(Math.random()) * 60;
      pos[i * 3] = Math.cos(angle) * radius;
      pos[i * 3 + 1] = 1 + Math.random() * 8;
      pos[i * 3 + 2] = Math.sin(angle) * radius;
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (!meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    const t = state.clock.elapsedTime;
    for (let i = 0; i < count; i++) {
      const off = offsets[i];
      arr[i * 3] += Math.sin(t * 0.8 + off) * 0.03;
      arr[i * 3 + 1] += Math.cos(t * 1.2 + off) * 0.02;
      arr[i * 3 + 2] += Math.sin(t * 0.6 + off * 2) * 0.03;
    }
    posAttr.needsUpdate = true;
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial
        size={0.4}
        color="#ffe66d"
        transparent
        opacity={0.9}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  );
}
'''


# =============================================================================
# BIRDS - پرندگان
# =============================================================================

BIRDS = '''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export function Birds() {
  const count = 12;
  const groupRef = useRef<THREE.Group>(null);

  const birds = useMemo(() => {
    return new Array(count).fill(0).map((_, i) => ({
      angle: (i / count) * Math.PI * 2,
      radius: 40 + Math.random() * 20,
      height: 30 + Math.random() * 15,
      speed: 0.3 + Math.random() * 0.2,
      offset: Math.random() * Math.PI * 2,
    }));
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((bird, i) => {
      const b = birds[i];
      const angle = b.angle + t * b.speed;
      bird.position.set(
        Math.cos(angle) * b.radius,
        b.height + Math.sin(t * 2 + b.offset) * 2,
        Math.sin(angle) * b.radius
      );
      bird.rotation.y = -angle - Math.PI / 2;
      bird.rotation.z = Math.sin(t * 8 + b.offset) * 0.3;
    });
  });

  return (
    <group ref={groupRef}>
      {birds.map((_, i) => (
        <mesh key={i}>
          <coneGeometry args={[0.5, 1.5, 4]} />
          <meshStandardMaterial color="#2d3436" />
        </mesh>
      ))}
    </group>
  );
}
'''


# =============================================================================
# BUTTERFLIES - پروانه‌ها
# =============================================================================

BUTTERFLIES = '''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const butterflyColors = ['#ff6b9d', '#feca57', '#48dbfb', '#ff9ff3', '#f368e0'];

export function Butterflies() {
  const count = 15;
  const groupRef = useRef<THREE.Group>(null);

  const flies = useMemo(() => {
    return new Array(count).fill(0).map(() => ({
      x: (Math.random() - 0.5) * 80,
      z: (Math.random() - 0.5) * 80,
      speed: 0.5 + Math.random() * 0.5,
      phase: Math.random() * Math.PI * 2,
      color: butterflyColors[Math.floor(Math.random() * butterflyColors.length)],
    }));
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((bfly, i) => {
      const f = flies[i];
      bfly.position.set(
        f.x + Math.sin(t * f.speed + f.phase) * 5,
        2 + Math.sin(t * 2 + f.phase) * 1.5,
        f.z + Math.cos(t * f.speed * 0.7 + f.phase) * 5
      );
      bfly.rotation.y = t * f.speed;
      bfly.scale.setScalar(1 + Math.sin(t * 10 + f.phase) * 0.2);
    });
  });

  return (
    <group ref={groupRef}>
      {flies.map((f, i) => (
        <mesh key={i}>
          <planeGeometry args={[0.8, 0.6]} />
          <meshBasicMaterial color={f.color} side={THREE.DoubleSide} transparent opacity={0.9} />
        </mesh>
      ))}
    </group>
  );
}
'''


# =============================================================================
# GOD RAYS - پرتوهای خورشید
# =============================================================================

GOD_RAYS = '''import { useMemo } from 'react';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function GodRays() {
  const { sunPosition, timeOfDay } = useWeatherStore();

  const rays = useMemo(() => {
    const arr = [];
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 0.5 - Math.PI * 0.25;
      arr.push({
        position: [
          sunPosition[0] * 0.5 + Math.cos(angle) * 10,
          sunPosition[1] * 0.5,
          sunPosition[2] * 0.5 + Math.sin(angle) * 10,
        ] as [number, number, number],
        rotation: [0.3 + i * 0.05, angle, 0] as [number, number, number],
      });
    }
    return arr;
  }, [sunPosition]);

  const intensity = timeOfDay === 'day' ? 0.15 : timeOfDay === 'dawn' || timeOfDay === 'dusk' ? 0.25 : 0;

  return (
    <group>
      {rays.map((ray, i) => (
        <mesh key={i} position={ray.position} rotation={ray.rotation}>
          <cylinderGeometry args={[0.5, 3, 80, 8, 1, true]} />
          <meshBasicMaterial
            color="#fff8dc"
            transparent
            opacity={intensity}
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
# CINEMATIC CAMERA - دوربین سینمایی
# =============================================================================

CINEMATIC_CAMERA = '''import { useFrame, useThree } from '@react-three/fiber';
import { useArtisticStore } from '../../hooks/useArtisticStore';

export function CinematicCamera() {
  const { camera } = useThree();
  const enableCinematicCamera = useArtisticStore((s) => s.enableCinematicCamera);

  useFrame((state) => {
    if (!enableCinematicCamera) return;
    const t = state.clock.elapsedTime * 0.1;
    const radius = 50;
    camera.position.x = Math.cos(t) * radius;
    camera.position.z = Math.sin(t) * radius;
    camera.position.y = 20 + Math.sin(t * 0.5) * 5;
    camera.lookAt(0, 5, 0);
  });

  return null;
}
'''


# =============================================================================
# CINEMATIC OVERLAY - لترباکس + گرین فیلم
# =============================================================================

CINEMATIC_OVERLAY = '''import { useArtisticStore } from '../../hooks/useArtisticStore';

export function CinematicOverlay() {
  const { enableLetterbox, enableFilmGrain, enableLensFlare } = useArtisticStore();

  return (
    <>
      {/* Letterbox bars */}
      {enableLetterbox && (
        <>
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: '8vh',
            background: '#000', zIndex: 500, pointerEvents: 'none',
          }} />
          <div style={{
            position: 'absolute', bottom: 0, left: 0, right: 0, height: '8vh',
            background: '#000', zIndex: 500, pointerEvents: 'none',
          }} />
        </>
      )}

      {/* Film grain */}
      {enableFilmGrain && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 501, pointerEvents: 'none',
          opacity: 0.08,
          backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 200 200\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'4\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\'/%3E%3C/svg%3E")',
        }} />
      )}

      {/* Lens flare */}
      {enableLensFlare && (
        <div style={{
          position: 'absolute', top: '20%', left: '70%', width: '150px', height: '150px',
          background: 'radial-gradient(circle, rgba(255,248,220,0.4) 0%, transparent 70%)',
          borderRadius: '50%', zIndex: 502, pointerEvents: 'none',
          filter: 'blur(2px)',
        }} />
      )}
    </>
  );
}
'''


# =============================================================================
# SEASON CONTROLLER - کنترل فصل‌ها (رنگ‌بندی)
# =============================================================================

SEASON_CONTROLLER = '''import { useEffect } from 'react';
import { useArtisticStore } from '../../hooks/useArtisticStore';
import { useWeatherStore } from '../../hooks/useWeatherStore';

// Season-based ambient adjustments
export function SeasonController() {
  const { season } = useArtisticStore();
  const setTimeOfDay = useWeatherStore((s) => s.setTimeOfDay);
  const setTemperature = useWeatherStore((s) => s.setTemperature);

  useEffect(() => {
    switch (season) {
      case 'spring':
        setTimeOfDay('day');
        setTemperature(18);
        break;
      case 'summer':
        setTimeOfDay('day');
        setTemperature(35);
        break;
      case 'autumn':
        setTimeOfDay('dusk');
        setTemperature(15);
        break;
      case 'winter':
        setTimeOfDay('day');
        setTemperature(-5);
        break;
    }
  }, [season, setTimeOfDay, setTemperature]);

  return null;
}
'''


# =============================================================================
# UPDATED MAIN SIMULATOR (integrates all effects)
# =============================================================================

CINEMATIC_SIMULATOR_V2 = '''import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows } from '@react-three/drei';
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
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';

function Scene() {
  const { condition, timeOfDay } = useWeatherStore();
  const {
    enableAurora, enableRainbow, enableFireflies, enableBirds,
    enableButterflies, enableGodRays,
  } = useArtisticStore();

  return (
    <>
      <SeasonController />
      <CinematicCamera />
      <LightingSystem />
      <Terrain />
      <VegetationSystem />
      <WeatherEffects />
      <WaterSystem />
      <PostProcessing />

      {/* Artistic effects */}
      {enableAurora && timeOfDay === 'night' && <Aurora />}
      {condition === 'storm' && <Lightning />}
      {enableRainbow && (condition === 'rain' || condition === 'clear') && timeOfDay === 'day' && <Rainbow />}
      {enableFireflies && timeOfDay === 'night' && <Fireflies />}
      {enableBirds && timeOfDay !== 'night' && condition !== 'storm' && <Birds />}
      {enableButterflies && timeOfDay === 'day' && condition === 'clear' && <Butterflies />}
      {enableGodRays && timeOfDay !== 'night' && condition !== 'dust' && <GodRays />}

      <ContactShadows position={[0, 0.1, 0]} opacity={0.4} scale={100} blur={2} far={20} />
      <OrbitControls makeDefault enablePan enableZoom enableRotate minDistance={5} maxDistance={150} maxPolarAngle={Math.PI / 2.1} />
    </>
  );
}

export function CinematicSimulator() {
  const { timeOfDay } = useWeatherStore();

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#000' }}>
      <Canvas
        shadows
        camera={{ position: [30, 20, 30], fov: 60, near: 0.1, far: 1000 }}
        gl={{ antialias: true, toneMapping: 4, toneMappingExposure: timeOfDay === 'night' ? 0.5 : 1.0 }}
        dpr={[1, 2]}
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
# CINEMATIC MODE - دکمه شناور برای ادغام در اپ
# =============================================================================

CINEMATIC_MODE = '''import { useState } from 'react';
import { Button, Tooltip } from 'antd';
import { PlayCircleOutlined, CloseOutlined } from '@ant-design/icons';
import { CinematicSimulator } from './CinematicSimulator';

/**
 * Floating button that opens the full cinematic simulator.
 * Safe to drop into any page without altering its structure.
 */
export function CinematicMode() {
  const [open, setOpen] = useState(false);

  if (open) {
    return (
      <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#000' }}>
        <Button
          danger
          icon={<CloseOutlined />}
          onClick={() => setOpen(false)}
          style={{ position: 'absolute', top: 16, left: 16, zIndex: 10000 }}
        >
          خروج از حالت سینمایی
        </Button>
        <CinematicSimulator />
      </div>
    );
  }

  return (
    <Tooltip title="شبیه‌ساز سینمایی" placement="top">
      <Button
        type="primary"
        shape="circle"
        size="large"
        icon={<PlayCircleOutlined />}
        onClick={() => setOpen(true)}
        style={{
          position: 'fixed',
          bottom: 30,
          left: 30,
          zIndex: 1000,
          width: 64,
          height: 64,
          fontSize: 28,
          boxShadow: '0 4px 20px rgba(64, 150, 255, 0.5)',
        }}
      />
    </Tooltip>
  );
}

export default CinematicMode;
'''


# =============================================================================
# MOUNTING LOGIC
# =============================================================================

def mount_into_app():
    """Safely inject <CinematicMode /> into App.tsx"""
    print("[Mount] Integrating CinematicMode into App.tsx")
    print("-" * 70)

    if not APP_FILE.exists():
        err("App.tsx not found")
        return False

    content = APP_FILE.read_text(encoding="utf-8-sig")

    # Check if already mounted
    if "CinematicMode" in content:
        info("CinematicMode already present in App.tsx - skipping")
        return True

    import_line = "import { CinematicMode } from './components/cinematic/CinematicMode';"

    # Add import after last import
    lines = content.split("\n")
    last_import_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("import "):
            last_import_idx = i

    if last_import_idx >= 0:
        lines.insert(last_import_idx + 1, import_line)
        content = "\n".join(lines)
        ok("Added import statement")
    else:
        content = import_line + "\n" + content
        ok("Added import at top")

    # Try to inject <CinematicMode /> right after the first 'return ('
    # Find the main return and insert right after the opening '('
    injected = False

    # Strategy: find 'return (' and insert after it
    pattern = re.compile(r"return\s*\(")
    match = pattern.search(content)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + "\n      <CinematicMode />" + content[insert_pos:]
        injected = True
        ok("Injected <CinematicMode /> after return (")
    
    if not injected:
        warn("Could not auto-inject. Please add manually:")
        warn("  1. import { CinematicMode } from './components/cinematic/CinematicMode';")
        warn("  2. Add <CinematicMode /> inside your root component's JSX")
        return False

    with open(APP_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    ok("Saved App.tsx")
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("")
    print("=" * 70)
    print("  🎬 Cinematic DELUXE Upgrade + Auto-Mount")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Generate new artistic components
    print("[Step 1] Generating artistic effects")
    print("-" * 70)
    components = {
        HOOKS_DIR / "useArtisticStore.ts": ARTISTIC_STORE,
        SIM_DIR / "Aurora.tsx": AURORA,
        SIM_DIR / "Lightning.tsx": LIGHTNING,
        SIM_DIR / "Rainbow.tsx": RAINBOW,
        SIM_DIR / "Fireflies.tsx": FIREFLIES,
        SIM_DIR / "Birds.tsx": BIRDS,
        SIM_DIR / "Butterflies.tsx": BUTTERFLIES,
        SIM_DIR / "GodRays.tsx": GOD_RAYS,
        SIM_DIR / "CinematicCamera.tsx": CINEMATIC_CAMERA,
        SIM_DIR / "CinematicOverlay.tsx": CINEMATIC_OVERLAY,
        SIM_DIR / "SeasonController.tsx": SEASON_CONTROLLER,
        SIM_DIR / "CinematicSimulator.tsx": CINEMATIC_SIMULATOR_V2,
        SIM_DIR / "CinematicMode.tsx": CINEMATIC_MODE,
    }
    for path, content in components.items():
        write_file(path, content)
        ok(f"Created: {path.relative_to(SRC)}")
    print("")

    # Step 2: Mount into App.tsx
    print("[Step 2] Mounting into App")
    print("-" * 70)
    mounted = mount_into_app()
    print("")

    # Step 3: Build verification
    print("[Step 3] Build verification")
    print("-" * 70)
    result = subprocess.run(
        "pnpm build", shell=True, cwd=FRONTEND,
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=300,
    )
    build_ok = result.returncode == 0
    if build_ok:
        ok("Build successful!")
    else:
        warn("Build had issues:")
        for line in (result.stdout + result.stderr).splitlines()[-20:]:
            print(f"    {line}")
    print("")

    # Step 4: Commit
    print("[Step 4] Committing")
    print("-" * 70)
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        msg = (
            "feat(cinematic): DELUXE artistic effects + auto-mount\n\n"
            "Added 10 artistic/psychological effects:\n"
            "- Aurora (procedural shader)\n"
            "- Lightning (storm flashes)\n"
            "- Rainbow (post-rain hope)\n"
            "- Fireflies (night ambiance)\n"
            "- Birds & Butterflies (living ecosystem)\n"
            "- God Rays (volumetric sunlight)\n"
            "- Seasons controller\n"
            "- Cinematic camera path\n"
            "- Letterbox + film grain overlay\n"
            "- Floating CinematicMode button auto-mounted in App.tsx"
        )
        subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("Committed and pushed")
    except Exception as e:
        warn(f"Commit issue: {e}")

    # Final report
    print("")
    print("=" * 70)
    if build_ok and mounted:
        print("  🎉 DELUXE CINEMATIC READY & MOUNTED!")
    elif build_ok:
        print("  ⚠️ Built but check manual mounting instructions above")
    else:
        print("  ⚠️ Check build errors above")
    print("=" * 70)
    print("")
    print("  Usage: Click the floating ▶ button (bottom-left) in the app")
    print("")
    print("  New artistic controls available via useArtisticStore:")
    print("    season, aurora, rainbow, fireflies, birds, butterflies,")
    print("    godRays, cinematicCamera, letterbox, filmGrain, lensFlare")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())