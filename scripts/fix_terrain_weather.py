#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Major Upgrade: Realistic Terrain + Storm/Dust Effects
======================================================
1. Terrain: 800x800 with multi-octave Perlin noise (mountains + valleys)
2. Dust Storm: Volumetric fog + dense particles + darkened sky
3. Storm: Lightning + heavy rain + strong wind + dark clouds
4. Camera: Far distance, wider FOV
5. Dynamic atmosphere based on weather condition
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
SIM_DIR = FRONTEND / "src" / "components" / "cinematic"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")


def setup_git_path():
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


# =============================================================================
# TERRAIN: 800x800 with multi-octave Perlin noise
# =============================================================================

TERRAIN = '''import { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

// Simple 2D Perlin noise implementation
class PerlinNoise {
  private permutation: number[];
  
  constructor(seed = 42) {
    this.permutation = [];
    for (let i = 0; i < 256; i++) this.permutation[i] = i;
    
    // Shuffle based on seed
    let n = seed;
    for (let i = 255; i > 0; i--) {
      n = (n * 9301 + 49297) % 233280;
      const j = Math.floor((n / 233280) * (i + 1));
      [this.permutation[i], this.permutation[j]] = [this.permutation[j], this.permutation[i]];
    }
    
    // Duplicate for overflow
    for (let i = 0; i < 256; i++) {
      this.permutation[256 + i] = this.permutation[i];
    }
  }
  
  private fade(t: number): number {
    return t * t * t * (t * (t * 6 - 15) + 10);
  }
  
  private lerp(t: number, a: number, b: number): number {
    return a + t * (b - a);
  }
  
  private grad(hash: number, x: number, y: number): number {
    const h = hash & 7;
    const u = h < 4 ? x : y;
    const v = h < 4 ? y : x;
    return ((h & 1) ? -u : u) + ((h & 2) ? -v : v);
  }
  
  noise2D(x: number, y: number): number {
    const X = Math.floor(x) & 255;
    const Y = Math.floor(y) & 255;
    
    x -= Math.floor(x);
    y -= Math.floor(y);
    
    const u = this.fade(x);
    const v = this.fade(y);
    
    const A = this.permutation[X] + Y;
    const B = this.permutation[X + 1] + Y;
    
    return this.lerp(
      v,
      this.lerp(u, this.grad(this.permutation[A], x, y), this.grad(this.permutation[B], x - 1, y)),
      this.lerp(u, this.grad(this.permutation[A + 1], x, y - 1), this.grad(this.permutation[B + 1], x - 1, y - 1))
    );
  }
  
  // Multi-octave fractal noise for natural terrain
  fbm(x: number, y: number, octaves: number = 4, lacunarity: number = 2.0, persistence: number = 0.5): number {
    let total = 0;
    let frequency = 1;
    let amplitude = 1;
    let maxValue = 0;
    
    for (let i = 0; i < octaves; i++) {
      total += this.noise2D(x * frequency, y * frequency) * amplitude;
      maxValue += amplitude;
      amplitude *= persistence;
      frequency *= lacunarity;
    }
    
    return total / maxValue;
  }
  
  // Ridged noise for sharp mountain peaks
  ridged(x: number, y: number, octaves: number = 4): number {
    let total = 0;
    let frequency = 1;
    let amplitude = 1;
    let maxValue = 0;
    
    for (let i = 0; i < octaves; i++) {
      const n = 1 - Math.abs(this.noise2D(x * frequency, y * frequency));
      total += n * n * amplitude;
      maxValue += amplitude;
      amplitude *= 0.5;
      frequency *= 2;
    }
    
    return total / maxValue;
  }
}

export function Terrain() {
  const meshRef = useRef<THREE.Mesh>(null);
  const { condition, plantGrowthStage } = useWeatherStore();
  
  // Terrain dimensions - MUCH LARGER
  const SIZE = 800;
  const SEGMENTS = 256;

  // Generate procedural heightmap with real topography
  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(SIZE, SIZE, SEGMENTS, SEGMENTS);
    const posAttr = geo.attributes.position;
    const colors = new Float32Array(posAttr.count * 3);
    
    const perlin = new PerlinNoise(42);
    
    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i);
      const z = posAttr.getY(i);
      
      // Normalize coordinates for noise
      const nx = x / SIZE;
      const nz = z / SIZE;
      
      // Multi-layered terrain generation
      // 1. Large-scale mountain ranges (ridged noise)
      const mountains = perlin.ridged(nx * 3 + 10, nz * 3 + 10, 4) * 40;
      
      // 2. Medium hills (fractal noise)
      const hills = perlin.fbm(nx * 5, nz * 5, 4, 2.0, 0.5) * 15;
      
      // 3. Small bumps for detail
      const bumps = perlin.fbm(nx * 20, nz * 20, 3, 2.0, 0.5) * 2;
      
      // 4. River valleys (carved by negative noise)
      const riverMask = Math.max(0, perlin.noise2D(nx * 2 + 5, nz * 2 + 5));
      const riverDepth = Math.pow(1 - riverMask, 3) * -8;
      
      // Combine all layers
      let height = mountains + hills + bumps + riverDepth;
      
      // Flatten near origin for visibility
      const distFromCenter = Math.sqrt(x * x + z * z);
      if (distFromCenter < 50) {
        const flattenFactor = Math.max(0, 1 - distFromCenter / 50);
        height *= (1 - flattenFactor * 0.7);
      }
      
      posAttr.setZ(i, height);
      
      // Color based on height and slope
      const normalizedHeight = (height + 10) / 50;
      
      let r, g, b;
      if (height < -3) {
        // Deep valley - dark earth
        r = 0.25; g = 0.20; b = 0.15;
      } else if (height < 2) {
        // Lowland - grass
        r = 0.25; g = 0.45; b = 0.20;
      } else if (height < 15) {
        // Hills - lighter grass
        r = 0.35; g = 0.55; b = 0.25;
      } else if (height < 30) {
        // High hills - rocky
        r = 0.45; g = 0.40; b = 0.35;
      } else {
        // Mountain peaks - grey/snow
        const snowFactor = Math.min(1, (height - 30) / 10);
        r = 0.5 + snowFactor * 0.4;
        g = 0.45 + snowFactor * 0.45;
        b = 0.4 + snowFactor * 0.5;
      }
      
      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }
    
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.computeVertexNormals();
    geo.rotateX(-Math.PI / 2);
    
    return geo;
  }, []);

  // Dynamic color overlay based on weather
  const colorOverlay = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#c4a574');
    if (condition === 'snow') return new THREE.Color('#e8e8f0');
    return null;
  }, [condition]);

  return (
    <mesh ref={meshRef} geometry={geometry} receiveShadow castShadow>
      <meshStandardMaterial
        vertexColors
        roughness={0.9}
        metalness={0.05}
        flatShading={false}
        color={colorOverlay || '#ffffff'}
      />
    </mesh>
  );
}
'''


# =============================================================================
# WEATHER EFFECTS: Realistic Dust Storm + Storm
# =============================================================================

WEATHER_EFFECTS = '''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

// ============ RAIN SYSTEM (Enhanced for Storm) ============
function Rain() {
  const { intensity, windSpeed, windDirection, condition } = useWeatherStore();
  const isStorm = condition === 'storm';
  const count = isStorm ? 15000 : 5000;
  const meshRef = useRef<THREE.Points>(null);

  const [positions, velocities] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 600;
      pos[i * 3 + 1] = Math.random() * 150 + 30;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 600;
      vel[i * 3 + 1] = isStorm ? -4 - Math.random() * 2 : -1.5 - Math.random() * 0.5;
    }
    return [pos, vel];
  }, [count, isStorm]);

  useFrame(() => {
    if (!meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    const windX = Math.cos((windDirection * Math.PI) / 180) * windSpeed * (isStorm ? 0.08 : 0.01);
    const windZ = Math.sin((windDirection * Math.PI) / 180) * windSpeed * (isStorm ? 0.08 : 0.01);
    
    for (let i = 0; i < count; i++) {
      arr[i * 3] += windX;
      arr[i * 3 + 1] += velocities[i * 3 + 1];
      arr[i * 3 + 2] += windZ;
      
      if (arr[i * 3 + 1] < 0) {
        arr[i * 3] = (Math.random() - 0.5) * 600;
        arr[i * 3 + 1] = Math.random() * 30 + 150;
        arr[i * 3 + 2] = (Math.random() - 0.5) * 600;
      }
    }
    posAttr.needsUpdate = true;
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial
        size={isStorm ? 0.25 : 0.15}
        color={isStorm ? "#c8d8e8" : "#a0c4ff"}
        transparent
        opacity={0.7 * intensity}
        depthWrite={false}
        sizeAttenuation
      />
    </points>
  );
}

// ============ DUST STORM (Volumetric) ============
function DustStorm() {
  const { intensity, windSpeed, windDirection } = useWeatherStore();
  
  // Multiple layers of dust for volumetric effect
  const dustLayers = useMemo(() => {
    const layers = [];
    
    // Layer 1: Fine particles (high density)
    const count1 = 8000;
    const pos1 = new Float32Array(count1 * 3);
    const vel1 = new Float32Array(count1 * 3);
    for (let i = 0; i < count1; i++) {
      pos1[i * 3] = (Math.random() - 0.5) * 800;
      pos1[i * 3 + 1] = Math.random() * 60;
      pos1[i * 3 + 2] = (Math.random() - 0.5) * 800;
      vel1[i * 3 + 1] = (Math.random() - 0.5) * 0.3;
    }
    layers.push({ count: count1, positions: pos1, velocities: vel1, size: 0.6, opacity: 0.4, speed: 1.5 });
    
    // Layer 2: Medium particles (swirling)
    const count2 = 4000;
    const pos2 = new Float32Array(count2 * 3);
    const vel2 = new Float32Array(count2 * 3);
    for (let i = 0; i < count2; i++) {
      pos2[i * 3] = (Math.random() - 0.5) * 800;
      pos2[i * 3 + 1] = Math.random() * 40 + 10;
      pos2[i * 3 + 2] = (Math.random() - 0.5) * 800;
      vel2[i * 3 + 1] = (Math.random() - 0.5) * 0.5;
    }
    layers.push({ count: count2, positions: pos2, velocities: vel2, size: 1.0, opacity: 0.5, speed: 1.2 });
    
    // Layer 3: Large debris (slow, heavy)
    const count3 = 1500;
    const pos3 = new Float32Array(count3 * 3);
    const vel3 = new Float32Array(count3 * 3);
    for (let i = 0; i < count3; i++) {
      pos3[i * 3] = (Math.random() - 0.5) * 800;
      pos3[i * 3 + 1] = Math.random() * 30;
      pos3[i * 3 + 2] = (Math.random() - 0.5) * 800;
      vel3[i * 3 + 1] = (Math.random() - 0.5) * 0.2;
    }
    layers.push({ count: count3, positions: pos3, velocities: vel3, size: 1.5, opacity: 0.3, speed: 0.8 });
    
    return layers;
  }, []);
  
  const refs = useRef<(THREE.Points | null)[]>([]);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const windX = Math.cos((windDirection * Math.PI) / 180) * windSpeed * 0.15;
    const windZ = Math.sin((windDirection * Math.PI) / 180) * windSpeed * 0.15;
    
    dustLayers.forEach((layer, layerIdx) => {
      const mesh = refs.current[layerIdx];
      if (!mesh) return;
      
      const posAttr = mesh.geometry.attributes.position as THREE.BufferAttribute;
      const arr = posAttr.array as Float32Array;
      
      for (let i = 0; i < layer.count; i++) {
        const turbulence = Math.sin(t * 2 + i * 0.1) * 0.5;
        arr[i * 3] += windX * layer.speed + turbulence * 0.3;
        arr[i * 3 + 1] += layer.velocities[i * 3 + 1] + Math.sin(t * 3 + i) * 0.1;
        arr[i * 3 + 2] += windZ * layer.speed + Math.cos(t * 2 + i) * 0.3;
        
        // Wrap around
        if (arr[i * 3] > 400) arr[i * 3] = -400;
        if (arr[i * 3] < -400) arr[i * 3] = 400;
        if (arr[i * 3 + 1] < 0) arr[i * 3 + 1] = 60;
        if (arr[i * 3 + 1] > 80) arr[i * 3 + 1] = 0;
        if (arr[i * 3 + 2] > 400) arr[i * 3 + 2] = -400;
        if (arr[i * 3 + 2] < -400) arr[i * 3 + 2] = 400;
      }
      posAttr.needsUpdate = true;
    });
  });

  return (
    <group>
      {dustLayers.map((layer, i) => (
        <points key={i} ref={(el) => { refs.current[i] = el; }}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={layer.count}
              array={layer.positions}
              itemSize={3}
            />
          </bufferGeometry>
          <pointsMaterial
            size={layer.size}
            color="#c9a66b"
            transparent
            opacity={layer.opacity * intensity}
            depthWrite={false}
            sizeAttenuation
            blending={THREE.NormalBlending}
          />
        </points>
      ))}
    </group>
  );
}

// ============ SNOW (Enhanced) ============
function Snow() {
  const { intensity, windSpeed } = useWeatherStore();
  const count = 5000;
  const meshRef = useRef<THREE.Points>(null);
  const offsets = useMemo(() => new Float32Array(count).map(() => Math.random() * Math.PI * 2), []);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 800;
      pos[i * 3 + 1] = Math.random() * 150 + 30;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 800;
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (!meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    const t = state.clock.elapsedTime;
    
    for (let i = 0; i < count; i++) {
      arr[i * 3] += Math.sin(t + offsets[i]) * 0.03 + windSpeed * 0.003;
      arr[i * 3 + 1] -= 0.2;
      arr[i * 3 + 2] += Math.cos(t + offsets[i]) * 0.03;
      
      if (arr[i * 3 + 1] < 0) {
        arr[i * 3] = (Math.random() - 0.5) * 800;
        arr[i * 3 + 1] = 150;
        arr[i * 3 + 2] = (Math.random() - 0.5) * 800;
      }
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
        color="#ffffff"
        transparent
        opacity={0.9 * intensity}
        depthWrite={false}
        sizeAttenuation
      />
    </points>
  );
}

// ============ WEATHER CONTROLLER ============
export function WeatherEffects() {
  const { condition } = useWeatherStore();

  return (
    <>
      {condition === 'rain' && <Rain />}
      {condition === 'snow' && <Snow />}
      {condition === 'dust' && <DustStorm />}
      {condition === 'storm' && (
        <>
          <Rain />
          <DustStorm />
        </>
      )}
    </>
  );
}
'''


# =============================================================================
# LIGHTING: Dynamic sky + volumetric fog for dust/storm
# =============================================================================

LIGHTING_SYSTEM = '''import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function LightingSystem() {
  const sunRef = useRef<THREE.DirectionalLight>(null);
  const { timeOfDay, sunPosition, condition, fogDensity, intensity } = useWeatherStore();

  // Dynamic fog with VOLUMETRIC density for dust/storm
  useFrame(({ scene }) => {
    if (!scene.fog) {
      scene.fog = new THREE.FogExp2('#cccccc', 0.005);
    }
    const fog = scene.fog as THREE.FogExp2;
    
    let targetDensity = fogDensity * 0.005;
    let fogColor = '#cccccc';
    
    if (condition === 'dust') {
      // DUST STORM: Heavy volumetric fog + brown tint
      targetDensity = 0.015 + intensity * 0.02;  // Very dense!
      fogColor = '#8b6f47';  // Brown dust
    } else if (condition === 'storm') {
      // STORM: Dense grey fog + darkness
      targetDensity = 0.012 + intensity * 0.015;
      fogColor = '#4a5568';  // Dark storm grey
    } else if (condition === 'snow') {
      targetDensity = 0.008;
      fogColor = '#d8dce8';
    } else if (condition === 'drought') {
      targetDensity = 0.004;
      fogColor = '#c4a574';
    } else if (condition === 'rain') {
      targetDensity = 0.008;
      fogColor = '#8a9aa8';
    } else if (timeOfDay === 'night') {
      fogColor = '#0a1520';
      targetDensity = 0.003;
    } else if (timeOfDay === 'dawn') {
      fogColor = '#ffb88c';
    } else if (timeOfDay === 'dusk') {
      fogColor = '#ff7e5f';
    }
    
    // Smooth interpolation
    fog.density += (targetDensity - fog.density) * 0.08;
    fog.color.lerp(new THREE.Color(fogColor), 0.08);
    scene.background = fog.color.clone();
  });

  // Sun intensity heavily reduced during dust/storm
  const sunIntensity = (() => {
    let base = 1.5;
    if (timeOfDay === 'night') base = 0.1;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 0.8;
    
    // DUST: Sun barely visible (orange/brown filtered)
    if (condition === 'dust') base *= 0.2 * (1 - intensity * 0.5);
    // STORM: Sun blocked by clouds
    if (condition === 'storm') base *= 0.15;
    if (condition === 'rain') base *= 0.5;
    if (condition === 'snow') base *= 0.7;
    
    return base;
  })();

  const sunColor = (() => {
    if (condition === 'dust') return '#d4935a';  // Orange-brown through dust
    if (condition === 'storm') return '#8a9aa8';  // Grey diffused
    if (timeOfDay === 'dawn') return '#ffb347';
    if (timeOfDay === 'dusk') return '#ff6b6b';
    if (timeOfDay === 'night') return '#4a6fa5';
    return '#fff8e7';
  })();

  // Sky parameters based on weather
  const skyRayleigh = (() => {
    if (condition === 'dust') return 8;  // Heavy scattering
    if (condition === 'storm') return 6;
    if (condition === 'rain') return 4;
    return 2;
  })();

  const skyMieCoefficient = (() => {
    if (condition === 'dust') return 0.15;  // Large particles
    if (condition === 'storm') return 0.1;
    return 0.005;
  })();

  return (
    <>
      {/* Main sun light */}
      <directionalLight
        ref={sunRef}
        position={sunPosition}
        intensity={sunIntensity}
        color={sunColor}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-200}
        shadow-camera-right={200}
        shadow-camera-top={200}
        shadow-camera-bottom={-200}
        shadow-camera-near={0.1}
        shadow-camera-far={800}
      />

      {/* Ambient light - reduced during storms */}
      <ambientLight 
        intensity={(() => {
          let base = timeOfDay === 'night' ? 0.15 : 0.4;
          if (condition === 'dust' || condition === 'storm') base *= 0.3;
          return base;
        })()} 
        color={sunColor} 
      />

      {/* Hemisphere light */}
      <hemisphereLight 
        args={[
          condition === 'dust' ? '#8b6f47' : '#87ceeb',
          '#3d5a3d',
          condition === 'dust' || condition === 'storm' ? 0.15 : 0.3
        ]} 
      />

      {/* Sky - darkened for dust/storm */}
      {timeOfDay !== 'night' && (
        <Sky
          distance={450000}
          sunPosition={sunPosition}
          inclination={0.5}
          azimuth={0.25}
          mieCoefficient={skyMieCoefficient}
          mieDirectionalG={condition === 'dust' ? 0.9 : 0.8}
          rayleigh={skyRayleigh}
          turbidity={condition === 'dust' ? 20 : condition === 'storm' ? 15 : 10}
        />
      )}

      {/* Stars at night */}
      {timeOfDay === 'night' && <Stars radius={500} depth={80} count={5000} factor={6} fade />}

      {/* Storm clouds - dark and dense */}
      {(condition === 'storm' || condition === 'rain') && (
        <>
          <Cloud position={[-60, 80, -100]} speed={0.6} opacity={0.9} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} />
          <Cloud position={[80, 90, -120]} speed={0.5} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} />
          <Cloud position={[0, 85, -150]} speed={0.7} opacity={0.95} color={condition === 'storm' ? '#1a202c' : '#6a7a88'} />
          <Cloud position={[-40, 75, -80]} speed={0.4} opacity={0.8} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} />
          <Cloud position={[60, 70, -60]} speed={0.5} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} />
        </>
      )}

      {/* Dust clouds - brown and low */}
      {condition === 'dust' && (
        <>
          <Cloud position={[-40, 25, -50]} speed={0.8} opacity={0.7} color="#8b6f47" />
          <Cloud position={[60, 30, -70]} speed={0.9} opacity={0.8} color="#a0826b" />
          <Cloud position={[0, 20, -90]} speed={1.0} opacity={0.75} color="#8b6f47" />
        </>
      )}
    </>
  );
}
'''


# =============================================================================
# MAIN SIMULATOR: Farther camera + wider FOV
# =============================================================================

CINEMATIC_SIMULATOR = '''import { Suspense } from 'react';
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

      {/* Artistic atmospheric effects */}
      {a.enableAurora && timeOfDay === 'night' && <Aurora />}
      {condition === 'storm' && <Lightning />}
      {a.enableRainbow && (condition === 'rain' || condition === 'clear') && timeOfDay === 'day' && <Rainbow />}
      {a.enableFireflies && timeOfDay === 'night' && <Fireflies />}
      {a.enableBirds && timeOfDay !== 'night' && condition !== 'storm' && condition !== 'dust' && <Birds />}
      {a.enableButterflies && timeOfDay === 'day' && condition === 'clear' && <Butterflies />}
      {a.enableGodRays && timeOfDay !== 'night' && condition !== 'dust' && condition !== 'storm' && <GodRays />}

      {/* Agricultural elements */}
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

      <ContactShadows position={[0, 0.1, 0]} opacity={0.4} scale={400} blur={3} far={50} />
      
      {/* Wider camera controls for larger terrain */}
      <OrbitControls 
        makeDefault 
        enablePan 
        enableZoom 
        enableRotate 
        minDistance={20}
        maxDistance={500}
        maxPolarAngle={Math.PI / 2.1}
        target={[0, 0, 0]}
      />
    </>
  );
}

export function CinematicSimulator() {
  const { timeOfDay } = useWeatherStore();

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#000' }}>
      <Canvas
        shadows
        camera={{ 
          position: [150, 80, 150],  // Much farther for 800x800 terrain
          fov: 70,  // Wider FOV
          near: 0.1, 
          far: 3000  // Extended far plane
        }}
        gl={{ 
          antialias: true, 
          toneMapping: 4, 
          toneMappingExposure: timeOfDay === 'night' ? 0.5 : 1.0 
        }}
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
# MAIN EXECUTION
# =============================================================================

def main():
    print("")
    print("=" * 70)
    print("  🌪️ Major Upgrade: Realistic Terrain + Storm/Dust Effects")
    print("=" * 70)
    print("")
    print("  Upgrades:")
    print("    🏔️ Terrain: 200x200 → 800x800 with mountains & valleys")
    print("    🌪️ Dust Storm: 3 layers of volumetric particles + dense fog")
    print("    ⛈️ Storm: 15K rain + lightning + dark clouds + strong wind")
    print("    🌅 Dynamic sky (brown for dust, grey for storm)")
    print("    📷 Camera: farther (150m) with wider FOV (70°)")
    print("")

    setup_git_path()

    # Generate files
    print("[Step 1] Writing upgraded components")
    print("-" * 70)
    
    files = {
        SIM_DIR / "Terrain.tsx": TERRAIN,
        SIM_DIR / "WeatherEffects.tsx": WEATHER_EFFECTS,
        SIM_DIR / "LightingSystem.tsx": LIGHTING_SYSTEM,
        SIM_DIR / "CinematicSimulator.tsx": CINEMATIC_SIMULATOR,
    }
    
    for path, content in files.items():
        write_file(path, content)
        ok(f"Updated: {path.relative_to(FRONTEND)}")
    
    print("")

    # Build
    print("[Step 2] Building project")
    print("-" * 70)
    info("This will take 1-2 minutes...")
    
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
            if "dist/assets/" in line and ("kB" in line or "MB" in line):
                if any(k in line for k in ["vendor", "index", "HyDroMaCenter"]):
                    print(f"    {line.strip()}")
    else:
        err("Build failed")
        print("\n  Error output (last 25 lines):")
        for line in (result.stdout + result.stderr).splitlines()[-25:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # Commit
    if build_ok:
        print("[Step 3] Committing")
        print("-" * 70)
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "feat(cinematic): realistic terrain + volumetric storm/dust\\n\\n"
                "Terrain upgrade:\\n"
                "- Size: 200x200 → 800x800 (16x area)\\n"
                "- Multi-octave Perlin noise for natural topography\\n"
                "- Ridged noise for sharp mountain peaks\\n"
                "- Carved river valleys\\n"
                "- Vertex colors based on height (grass/rock/snow)\\n"
                "- 256x256 segments for detail\\n\\n"
                "Dust Storm (realistic):\\n"
                "- 3 volumetric dust layers (13,500 particles total)\\n"
                "- Heavy volumetric fog (density 0.015-0.035)\\n"
                "- Brown-tinted sky with high turbidity\\n"
                "- Reduced sun intensity (20% normal)\\n"
                "- Strong wind particles (15x speed)\\n\\n"
                "Storm (enhanced):\\n"
                "- 15,000 rain particles (3x normal)\\n"
                "- Dark grey clouds (5 layers)\\n"
                "- Fog density 0.012-0.027\\n"
                "- Lightning system active\\n"
                "- Reduced ambient lighting\\n\\n"
                "Camera:\\n"
                "- Position: (150, 80, 150) - farther for larger terrain\\n"
                "- FOV: 70° (wider view)\\n"
                "- Max distance: 500 units\\n"
                "- Far plane: 3000 units\\n\\n"
                "Visit: http://localhost:5173/hydroma"
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")
        
        print("")
        print("=" * 70)
        print("  🎉 UPGRADE COMPLETE!")
        print("=" * 70)
        print("")
        print("  Test in browser:")
        print("    cd D:\\eco_nojin\\frontend")
        print("    pnpm dev")
        print("    Visit: http://localhost:5173/hydroma")
        print("")
        print("  🏔️ Try these scenarios:")
        print("    1. Select 'ریزگرد' (Dust) - see brown volumetric fog")
        print("    2. Select 'طوفان' (Storm) - see lightning + heavy rain")
        print("    3. Pan camera to see mountains and valleys")
        print("    4. Zoom out to see full 800x800 terrain")
        print("    5. Try 'شب' (Night) with 'شفق قطبی' (Aurora)")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())