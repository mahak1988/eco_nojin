#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultra HD Render Quality Upgrade
================================
1. Canvas: DPR [2,3] + WebGL2 + highp precision
2. Shadows: 4096x4096 + PCF soft shadows
3. Post-processing: High-quality N8AO + Bloom + SSAO
4. Textures: Anisotropic filtering 16x
5. Terrain: Better normals + detail
6. Sky: Enhanced resolution
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
# CINEMATIC SIMULATOR - Ultra HD Canvas
# =============================================================================

CINEMATIC_SIMULATOR_UHD = '''import { Suspense, useEffect } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, ContactShadows, Preload } from '@react-three/drei';
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

/**
 * Quality enhancer component - applies anisotropic filtering to all textures
 * and optimizes renderer settings for ultra HD output
 */
function QualityEnhancer() {
  const { gl, scene } = useThree();

  useEffect(() => {
    // Enable high-quality texture filtering
    const maxAniso = gl.capabilities.getMaxAnisotropy();
    
    scene.traverse((obj) => {
      if ((obj as THREE.Mesh).isMesh) {
        const mesh = obj as THREE.Mesh;
        const mat = mesh.material as THREE.Material & { map?: THREE.Texture; normalMap?: THREE.Texture };
        
        if (mat.map) {
          mat.map.anisotropy = Math.min(16, maxAniso);
          mat.map.minFilter = THREE.LinearMipmapLinearFilter;
          mat.map.magFilter = THREE.LinearFilter;
          mat.map.generateMipmaps = true;
          mat.map.needsUpdate = true;
        }
        
        if (mat.normalMap) {
          mat.normalMap.anisotropy = Math.min(16, maxAniso);
          mat.normalMap.needsUpdate = true;
        }
      }
    });

    // Renderer optimizations
    gl.outputColorSpace = THREE.SRGBColorSpace;
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.1;
    
    // Enable physically correct lights
    gl.physicallyCorrectLights = true;
    
    console.log(`🎬 UHD Render Quality Active: Anisotropy=${Math.min(16, maxAniso)}x`);
  }, [gl, scene]);

  return null;
}

function Scene() {
  const { condition, timeOfDay } = useWeatherStore();
  const a = useArtisticStore();

  return (
    <>
      <QualityEnhancer />
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

      {/* Enhanced contact shadows - softer and wider */}
      <ContactShadows 
        position={[0, 0.05, 0]} 
        opacity={0.5} 
        scale={600} 
        blur={2.5} 
        far={80}
        resolution={1024}
        color="#1a2a3a"
      />
      
      <OrbitControls 
        makeDefault 
        enablePan 
        enableZoom 
        enableRotate 
        minDistance={20}
        maxDistance={600}
        maxPolarAngle={Math.PI / 2.05}
        target={[0, 0, 0]}
        enableDamping
        dampingFactor={0.05}
      />
      
      <Preload all />
    </>
  );
}

export function CinematicSimulator() {
  const { timeOfDay, condition } = useWeatherStore();

  // Dynamic exposure based on weather/time
  const exposure = (() => {
    let base = 1.1;
    if (timeOfDay === 'night') base = 0.6;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 0.9;
    if (condition === 'dust') base *= 0.5;
    if (condition === 'storm') base *= 0.4;
    return base;
  })();

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#000' }}>
      <Canvas
        shadows="soft"
        camera={{ 
          position: [150, 80, 150],
          fov: 65,  // Slightly narrower for more cinematic look
          near: 0.1, 
          far: 5000
        }}
        gl={{ 
          antialias: true,
          alpha: false,
          powerPreference: 'high-performance',
          stencil: false,
          depth: true,
          preserveDrawingBuffer: false,
          logarithmicDepthBuffer: true,  // Better z-fighting prevention
        }}
        dpr={[2, 3]}  // Ultra HD: 2x to 3x device pixel ratio
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = exposure;
          gl.outputColorSpace = THREE.SRGBColorSpace;
          // Enable shadow map
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
      
      {/* UHD Quality Indicator */}
      <div style={{
        position: 'absolute',
        bottom: 10,
        left: 10,
        color: 'rgba(255,255,255,0.5)',
        fontSize: 11,
        fontFamily: 'monospace',
        pointerEvents: 'none',
        zIndex: 100,
      }}>
        🎬 UHD RENDER ACTIVE | DPR: {window.devicePixelRatio.toFixed(1)}x | PCF Soft Shadows
      </div>
    </div>
  );
}

export default CinematicSimulator;
'''


# =============================================================================
# POST-PROCESSING - Ultra Quality
# =============================================================================

POST_PROCESSING_UHD = '''import { EffectComposer, Bloom, DepthOfField, Vignette, ChromaticAberration, HueSaturation, BrightnessContrast } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import { N8AO } from '@react-three/postprocessing';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';
import { Vector2 } from 'three';

export function PostProcessing() {
  const { enablePostProcessing, condition, timeOfDay } = useArtisticStore();
  const weather = useWeatherStore();

  if (!enablePostProcessing) return null;

  // Color grading based on weather
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

  const brightness = (() => {
    if (weather.condition === 'storm' || weather.condition === 'dust') return -0.15;
    if (weather.timeOfDay === 'night') return -0.2;
    return 0;
  })();

  const contrast = (() => {
    if (weather.timeOfDay === 'dawn' || weather.timeOfDay === 'dusk') return 0.15;
    if (weather.condition === 'dust') return -0.1;
    return 0.05;
  })();

  return (
    <EffectComposer 
      multisampling={8}  // 8x MSAA for ultra-smooth edges
      frameBufferType={THREE.HalfFloatType}  // HDR rendering
    >
      {/* Ultra quality SSAO via N8AO */}
      <N8AO
        aoRadius={0.8}
        intensity={2.5}
        distanceFalloff={0.8}
        color="#1a1a2e"
        quality="ultra"  // Ultra quality preset
        halfRes={false}  // Full resolution
      />

      {/* Enhanced Bloom with mipmapped blur */}
      <Bloom
        intensity={weather.timeOfDay === 'night' ? 1.2 : 0.5}
        luminanceThreshold={0.75}
        luminanceSmoothing={0.85}
        mipmapBlur
        radius={0.85}
        levels={8}
      />

      {/* Cinematic Depth of Field */}
      <DepthOfField
        focusDistance={0.015}
        focalLength={0.04}
        bokehScale={2.5}
        height={720}
      />

      {/* Brightness & Contrast for cinematic look */}
      <BrightnessContrast
        brightness={brightness}
        contrast={contrast}
      />

      {/* Color grading */}
      <HueSaturation
        hue={hueShift}
        saturation={saturation}
      />

      {/* Cinematic Vignette */}
      <Vignette
        eskil={false}
        offset={0.25}
        darkness={0.85}
      />

      {/* Chromatic aberration for storm/dust */}
      {(weather.condition === 'storm' || weather.condition === 'dust') && (
        <ChromaticAberration
          offset={new Vector2(0.0015, 0.0015)}
          radialModulation={true}
          modulationOffset={0.5}
        />
      )}
    </EffectComposer>
  );
}
'''


# =============================================================================
# LIGHTING SYSTEM - Ultra Shadows
# =============================================================================

LIGHTING_SYSTEM_UHD = '''import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function LightingSystem() {
  const sunRef = useRef<THREE.DirectionalLight>(null);
  const fillLightRef = useRef<THREE.DirectionalLight>(null);
  const { timeOfDay, sunPosition, condition, fogDensity, intensity } = useWeatherStore();

  // Configure ultra-quality shadows
  useFrame(() => {
    if (sunRef.current) {
      const shadow = sunRef.current.shadow;
      shadow.mapSize.width = 4096;  // Ultra HD shadows
      shadow.mapSize.height = 4096;
      shadow.camera.near = 1;
      shadow.camera.far = 1500;
      shadow.camera.left = -400;
      shadow.camera.right = 400;
      shadow.camera.top = 400;
      shadow.camera.bottom = -400;
      shadow.bias = -0.0001;  // Reduced shadow acne
      shadow.normalBias = 0.05;
      shadow.radius = 3;  // Soft shadow edges
      shadow.blurSamples = 16;  // High-quality soft shadows
    }
  });

  // Dynamic fog with VOLUMETRIC density
  useFrame(({ scene }) => {
    if (!scene.fog) {
      scene.fog = new THREE.FogExp2('#cccccc', 0.005);
    }
    const fog = scene.fog as THREE.FogExp2;
    
    let targetDensity = fogDensity * 0.005;
    let fogColor = '#cccccc';
    
    if (condition === 'dust') {
      targetDensity = 0.015 + intensity * 0.02;
      fogColor = '#8b6f47';
    } else if (condition === 'storm') {
      targetDensity = 0.012 + intensity * 0.015;
      fogColor = '#4a5568';
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
    
    fog.density += (targetDensity - fog.density) * 0.08;
    fog.color.lerp(new THREE.Color(fogColor), 0.08);
    scene.background = fog.color.clone();
  });

  const sunIntensity = (() => {
    let base = 2.0;  // Increased for physically correct lights
    if (timeOfDay === 'night') base = 0.15;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 1.0;
    if (condition === 'dust') base *= 0.2 * (1 - intensity * 0.5);
    if (condition === 'storm') base *= 0.15;
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

  const skyRayleigh = (() => {
    if (condition === 'dust') return 8;
    if (condition === 'storm') return 6;
    if (condition === 'rain') return 4;
    return 2;
  })();

  const skyMieCoefficient = (() => {
    if (condition === 'dust') return 0.15;
    if (condition === 'storm') return 0.1;
    return 0.005;
  })();

  return (
    <>
      {/* Main sun - Ultra HD shadows */}
      <directionalLight
        ref={sunRef}
        position={sunPosition}
        intensity={sunIntensity}
        color={sunColor}
        castShadow
      />

      {/* Fill light (reduces harsh shadows) */}
      <directionalLight
        ref={fillLightRef}
        position={[-sunPosition[0] * 0.5, sunPosition[1] * 0.3, -sunPosition[2] * 0.5]}
        intensity={sunIntensity * 0.15}
        color={sunColor}
      />

      {/* Ambient light */}
      <ambientLight 
        intensity={(() => {
          let base = timeOfDay === 'night' ? 0.2 : 0.5;
          if (condition === 'dust' || condition === 'storm') base *= 0.3;
          return base;
        })()} 
        color={sunColor} 
      />

      {/* Hemisphere light for natural sky/ground color */}
      <hemisphereLight 
        args={[
          condition === 'dust' ? '#8b6f47' : '#b8d4e8',
          condition === 'drought' ? '#8b6f47' : '#4a7c3a',
          condition === 'dust' || condition === 'storm' ? 0.2 : 0.5
        ]} 
      />

      {/* Enhanced Sky - farther distance, better resolution */}
      {timeOfDay !== 'night' && (
        <Sky
          distance={1000000}  // 1M distance for deeper sky
          sunPosition={sunPosition}
          inclination={0.5}
          azimuth={0.25}
          mieCoefficient={skyMieCoefficient}
          mieDirectionalG={condition === 'dust' ? 0.9 : 0.8}
          rayleigh={skyRayleigh}
          turbidity={condition === 'dust' ? 20 : condition === 'storm' ? 15 : 8}
        />
      )}

      {/* Stars at night - more stars, bigger radius */}
      {timeOfDay === 'night' && (
        <Stars 
          radius={800} 
          depth={100} 
          count={8000} 
          factor={6} 
          saturation={0.2}
          fade 
          speed={0.5}
        />
      )}

      {/* Storm clouds */}
      {(condition === 'storm' || condition === 'rain') && (
        <>
          <Cloud position={[-60, 80, -100]} speed={0.6} opacity={0.9} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} segments={40} />
          <Cloud position={[80, 90, -120]} speed={0.5} opacity={0.85} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} segments={40} />
          <Cloud position={[0, 85, -150]} speed={0.7} opacity={0.95} color={condition === 'storm' ? '#1a202c' : '#6a7a88'} segments={40} />
        </>
      )}

      {/* Dust clouds */}
      {condition === 'dust' && (
        <>
          <Cloud position={[-40, 25, -50]} speed={0.8} opacity={0.7} color="#8b6f47" segments={30} />
          <Cloud position={[60, 30, -70]} speed={0.9} opacity={0.8} color="#a0826b" segments={30} />
        </>
      )}
    </>
  );
}
'''


# =============================================================================
# TERRAIN - Enhanced Detail
# =============================================================================

TERRAIN_UHD = '''import { useRef, useMemo } from 'react';
import * as THREE from 'three';
import { useWeatherStore } from '../../hooks/useWeatherStore';

// Perlin noise class (same as before)
class PerlinNoise {
  private permutation: number[];
  
  constructor(seed = 42) {
    this.permutation = [];
    for (let i = 0; i < 256; i++) this.permutation[i] = i;
    let n = seed;
    for (let i = 255; i > 0; i--) {
      n = (n * 9301 + 49297) % 233280;
      const j = Math.floor((n / 233280) * (i + 1));
      [this.permutation[i], this.permutation[j]] = [this.permutation[j], this.permutation[i]];
    }
    for (let i = 0; i < 256; i++) this.permutation[256 + i] = this.permutation[i];
  }
  
  private fade(t: number): number { return t * t * t * (t * (t * 6 - 15) + 10); }
  private lerp(t: number, a: number, b: number): number { return a + t * (b - a); }
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
    return this.lerp(v,
      this.lerp(u, this.grad(this.permutation[A], x, y), this.grad(this.permutation[B], x - 1, y)),
      this.lerp(u, this.grad(this.permutation[A + 1], x, y - 1), this.grad(this.permutation[B + 1], x - 1, y - 1))
    );
  }
  
  fbm(x: number, y: number, octaves: number = 4): number {
    let total = 0, frequency = 1, amplitude = 1, maxValue = 0;
    for (let i = 0; i < octaves; i++) {
      total += this.noise2D(x * frequency, y * frequency) * amplitude;
      maxValue += amplitude;
      amplitude *= 0.5;
      frequency *= 2;
    }
    return total / maxValue;
  }
  
  ridged(x: number, y: number, octaves: number = 4): number {
    let total = 0, frequency = 1, amplitude = 1, maxValue = 0;
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
  
  const SIZE = 800;
  const SEGMENTS = 256;  // High detail

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(SIZE, SIZE, SEGMENTS, SEGMENTS);
    const posAttr = geo.attributes.position;
    const colors = new Float32Array(posAttr.count * 3);
    
    const perlin = new PerlinNoise(42);
    
    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i);
      const z = posAttr.getY(i);
      const nx = x / SIZE;
      const nz = z / SIZE;
      
      const mountains = perlin.ridged(nx * 3 + 10, nz * 3 + 10, 4) * 40;
      const hills = perlin.fbm(nx * 5, nz * 5, 4) * 15;
      const bumps = perlin.fbm(nx * 20, nz * 20, 3) * 2;
      const riverMask = Math.max(0, perlin.noise2D(nx * 2 + 5, nz * 2 + 5));
      const riverDepth = Math.pow(1 - riverMask, 3) * -8;
      
      let height = mountains + hills + bumps + riverDepth;
      
      const distFromCenter = Math.sqrt(x * x + z * z);
      if (distFromCenter < 50) {
        const flattenFactor = Math.max(0, 1 - distFromCenter / 50);
        height *= (1 - flattenFactor * 0.7);
      }
      
      posAttr.setZ(i, height);
      
      // Enhanced color palette with more variety
      let r, g, b;
      if (height < -3) {
        // Deep valley - dark rich earth
        r = 0.22; g = 0.18; b = 0.12;
      } else if (height < 1) {
        // River bank - sandy
        const sand = perlin.fbm(nx * 40, nz * 40, 2) * 0.1;
        r = 0.55 + sand; g = 0.48 + sand; b = 0.35 + sand;
      } else if (height < 5) {
        // Lowland grass - lush green
        const grass = perlin.fbm(nx * 30, nz * 30, 2) * 0.08;
        r = 0.25 + grass; g = 0.50 + grass * 2; b = 0.20 + grass;
      } else if (height < 15) {
        // Hills - medium green
        const variation = perlin.fbm(nx * 25, nz * 25, 2) * 0.1;
        r = 0.35 + variation; g = 0.55 + variation; b = 0.25 + variation;
      } else if (height < 25) {
        // High hills - rocky grass
        const rock = perlin.fbm(nx * 15, nz * 15, 2) * 0.1;
        r = 0.45 + rock; g = 0.42 + rock; b = 0.35 + rock;
      } else if (height < 35) {
        // Rocky mountains
        const rock = perlin.fbm(nx * 10, nz * 10, 3) * 0.1;
        r = 0.50 + rock; g = 0.48 + rock; b = 0.45 + rock;
      } else {
        // Snow peaks
        const snowFactor = Math.min(1, (height - 35) / 8);
        const snowNoise = perlin.fbm(nx * 20, nz * 20, 2) * 0.1;
        r = 0.55 + snowFactor * 0.4 + snowNoise;
        g = 0.52 + snowFactor * 0.43 + snowNoise;
        b = 0.48 + snowFactor * 0.47 + snowNoise;
      }
      
      colors[i * 3] = r;
      colors[i * 3 + 1] = g;
      colors[i * 3 + 2] = b;
    }
    
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.computeVertexNormals();  // Smooth normals for better lighting
    geo.rotateX(-Math.PI / 2);
    
    return geo;
  }, []);

  const colorOverlay = useMemo(() => {
    if (condition === 'drought') return new THREE.Color('#c4a574');
    if (condition === 'snow') return new THREE.Color('#e8e8f0');
    return null;
  }, [condition]);

  return (
    <mesh ref={meshRef} geometry={geometry} receiveShadow castShadow>
      <meshStandardMaterial
        vertexColors
        roughness={0.85}
        metalness={0.02}
        flatShading={false}
        color={colorOverlay || '#ffffff'}
        envMapIntensity={0.5}
      />
    </mesh>
  );
}
'''


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("")
    print("=" * 70)
    print("  🎬 Ultra HD Render Quality Upgrade")
    print("=" * 70)
    print("")
    print("  Upgrades:")
    print("    🖥️  DPR: [2,3] for ultra-sharp pixels")
    print("    🌑 Shadows: 4096×4096 PCF Soft")
    print("    🎨 MSAA: 8x anti-aliasing")
    print("    🌈 HDR: HalfFloat frame buffer")
    print("    🔍 Anisotropic: 16x texture filtering")
    print("    📐 Logarithmic Depth Buffer: no z-fighting")
    print("    💡 Fill Light: reduced harsh shadows")
    print("    ⭐ Stars: 8000 stars at night")
    print("    🎬 ACES Filmic + Enhanced Tone Mapping")
    print("")

    setup_git_path()

    # Write upgraded files
    print("[Step 1] Writing UHD components")
    print("-" * 70)
    
    files = {
        SIM_DIR / "CinematicSimulator.tsx": CINEMATIC_SIMULATOR_UHD,
        SIM_DIR / "PostProcessing.tsx": POST_PROCESSING_UHD,
        SIM_DIR / "LightingSystem.tsx": LIGHTING_SYSTEM_UHD,
        SIM_DIR / "Terrain.tsx": TERRAIN_UHD,
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
                "feat(render): ultra HD quality upgrade\\n\\n"
                "Canvas:\\n"
                "- DPR: [2,3] for ultra-sharp pixels\\n"
                "- MSAA: 8x anti-aliasing in post-processing\\n"
                "- HDR: HalfFloat frame buffer\\n"
                "- Logarithmic depth buffer (no z-fighting)\\n"
                "- Power preference: high-performance\\n\\n"
                "Shadows:\\n"
                "- 4096×4096 shadow map (4x previous)\\n"
                "- PCF Soft Shadow mapping\\n"
                "- 16 blur samples for smooth edges\\n"
                "- Reduced bias for accurate shadows\\n\\n"
                "Lighting:\\n"
                "- Fill light for softer shadows\\n"
                "- Physically correct lights enabled\\n"
                "- Enhanced ACES Filmic tone mapping\\n"
                "- Dynamic exposure based on weather\\n\\n"
                "Textures:\\n"
                "- Anisotropic filtering 16x\\n"
                "- Linear Mipmap Linear filtering\\n"
                "- sRGB color space output\\n\\n"
                "Post-Processing:\\n"
                "- N8AO ultra quality preset\\n"
                "- Enhanced bloom with mipmapped blur\\n"
                "- Brightness/Contrast control\\n"
                "- Cinematic vignette\\n\\n"
                "Terrain:\\n"
                "- Enhanced color palette (sand, grass, rock, snow)\\n"
                "- Perlin noise variation for natural look\\n"
                "- Smooth normals for better lighting\\n\\n"
                "Sky:\\n"
                "- Distance: 1M (deeper sky)\\n"
                "- 8000 stars at night (was 5000)\\n"
                "- Enhanced cloud segments\\n\\n"
                "Visit: http://localhost:5173/hydroma"
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")
        
        print("")
        print("=" * 70)
        print("  🎉 UHD UPGRADE COMPLETE!")
        print("=" * 70)
        print("")
        print("  Test in browser:")
        print("    cd D:\\eco_nojin\\frontend")
        print("    pnpm dev")
        print("    Visit: http://localhost:5173/hydroma")
        print("")
        print("  🎬 Quality improvements you'll see:")
        print("    ✅ Sharp, non-pixelated edges (DPR 2-3x)")
        print("    ✅ Soft, realistic shadows (PCF 4096)")
        print("    ✅ Smooth color gradients (HDR + MSAA)")
        print("    ✅ Clear textures from all angles (Anisotropic 16x)")
        print("    ✅ No z-fighting on distant terrain")
        print("    ✅ Cinematic color grading (ACES Filmic)")
        print("    ✅ Rich terrain colors (sand/grass/rock/snow)")
        print("    ✅ Deep night sky with 8000 stars")
        print("")
        print("  🖥️  Performance note:")
        print("    UHD quality requires decent GPU. If FPS drops,")
        print("    reduce DPR in CinematicSimulator.tsx: dpr={[1.5, 2]}")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())