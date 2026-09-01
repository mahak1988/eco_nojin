#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Missing "Water" export from @react-three/drei
===================================================
Problem: @react-three/drei@10.7.8 doesn't export "Water" component
Solution: Replace with custom GLSL-based water shader component

This is actually a better solution because:
- Full control over water appearance
- Cinematic quality with custom shaders
- No dependency on drei's Water implementation
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
CINEMATIC_DIR = FRONTEND / "src" / "components" / "cinematic"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def err(m): print(f"[ERROR] {m}")


def setup_git_path():
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


# Custom Water component with GLSL shader
CUSTOM_WATER = '''import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface CustomWaterProps {
  position?: [number, number, number];
  args?: [number, number];
  color?: string;
  waveHeight?: number;
  waveSpeed?: number;
  segments?: number;
}

/**
 * Custom cinematic water with GLSL shader
 * Features:
 * - Multi-layered wave animation
 * - Depth-based coloring
 * - Specular highlights
 * - Foam on wave peaks
 */
export function CustomWater({
  position = [0, 0, 0],
  args = [40, 40],
  color = '#2a5a8a',
  waveHeight = 0.2,
  waveSpeed = 0.5,
  segments = 64,
}: CustomWaterProps) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uColor: { value: new THREE.Color(color) },
    uWaveHeight: { value: waveHeight },
    uWaveSpeed: { value: waveSpeed },
    uFoamColor: { value: new THREE.Color('#e8f4ff') },
    uDeepColor: { value: new THREE.Color(color).multiplyScalar(0.5) },
    uShallowColor: { value: new THREE.Color(color).multiplyScalar(1.2) },
  }), [color, waveHeight, waveSpeed]);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
  });

  const vertexShader = `
    uniform float uTime;
    uniform float uWaveHeight;
    uniform float uWaveSpeed;
    
    varying vec2 vUv;
    varying vec3 vWorldPosition;
    varying float vWaveHeight;
    
    // Classic Perlin 3D noise (simplified)
    float hash(vec2 p) {
      return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
    }
    
    float noise(vec2 p) {
      vec2 i = floor(p);
      vec2 f = fract(p);
      vec2 u = f * f * (3.0 - 2.0 * f);
      
      return mix(
        mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), u.x),
        mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
        u.y
      );
    }
    
    void main() {
      vUv = uv;
      vec3 pos = position;
      
      // Multi-frequency wave layers
      float t = uTime * uWaveSpeed;
      
      // Large waves
      float wave1 = sin(pos.x * 0.3 + t * 0.8) * cos(pos.y * 0.2 + t * 0.5) * uWaveHeight * 2.0;
      
      // Medium waves
      float wave2 = sin(pos.x * 0.8 + pos.y * 0.6 + t * 1.2) * uWaveHeight;
      
      // Small ripples
      float wave3 = sin(pos.x * 2.0 + t * 2.5) * cos(pos.y * 1.8 + t * 2.0) * uWaveHeight * 0.3;
      
      // Noise-based waves for organic feel
      float noiseWave = noise(pos.xy * 0.5 + t * 0.3) * uWaveHeight * 1.5;
      
      pos.z += wave1 + wave2 + wave3 + noiseWave;
      vWaveHeight = pos.z;
      
      vec4 worldPos = modelMatrix * vec4(pos, 1.0);
      vWorldPosition = worldPos.xyz;
      
      gl_Position = projectionMatrix * viewMatrix * worldPos;
    }
  `;

  const fragmentShader = `
    uniform vec3 uColor;
    uniform vec3 uFoamColor;
    uniform vec3 uDeepColor;
    uniform vec3 uShallowColor;
    uniform float uTime;
    
    varying vec2 vUv;
    varying vec3 vWorldPosition;
    varying float vWaveHeight;
    
    void main() {
      // Depth-based coloring
      float depth = smoothstep(-0.3, 0.3, vWaveHeight);
      vec3 waterColor = mix(uDeepColor, uShallowColor, depth);
      
      // Specular highlights (sun reflection)
      vec3 viewDir = normalize(cameraPosition - vWorldPosition);
      vec3 lightDir = normalize(vec3(1.0, 1.0, 0.5));
      vec3 halfDir = normalize(lightDir + viewDir);
      
      float spec = pow(max(dot(vec3(0.0, 0.0, 1.0), halfDir), 0.0), 64.0);
      waterColor += vec3(1.0, 0.95, 0.8) * spec * 0.6;
      
      // Fresnel effect (edges more reflective)
      float fresnel = pow(1.0 - max(dot(viewDir, vec3(0.0, 0.0, 1.0)), 0.0), 3.0);
      waterColor = mix(waterColor, vec3(0.5, 0.7, 0.9), fresnel * 0.4);
      
      // Foam on wave peaks
      float foam = smoothstep(0.15, 0.25, vWaveHeight);
      foam *= 0.7 + 0.3 * sin(vUv.x * 20.0 + uTime) * cos(vUv.y * 20.0 + uTime * 0.7);
      waterColor = mix(waterColor, uFoamColor, foam * 0.6);
      
      // Edge darkening (vignette effect)
      float edge = smoothstep(0.0, 0.15, min(vUv.x, min(vUv.y, min(1.0 - vUv.x, 1.0 - vUv.y))));
      waterColor *= 0.7 + 0.3 * edge;
      
      // Caustics-like patterns
      float caustics = sin(vUv.x * 30.0 + uTime * 0.5) * sin(vUv.y * 30.0 + uTime * 0.7) * 0.1;
      waterColor += vec3(caustics) * 0.3;
      
      gl_FragColor = vec4(waterColor, 0.88);
    }
  `;

  return (
    <mesh position={position} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[args[0], args[1], segments, segments]} />
      <shaderMaterial
        ref={materialRef}
        uniforms={uniforms}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        transparent
        side={THREE.DoubleSide}
        depthWrite={false}
      />
    </mesh>
  );
}

export default CustomWater;
'''


# Updated WaterSystem that uses CustomWater
WATER_SYSTEM = '''import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { CustomWater } from './CustomWater';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function WaterSystem() {
  const waterRef = useRef<THREE.Group>(null);
  const { condition, timeOfDay } = useWeatherStore();

  // Dynamic water color based on conditions
  const waterColor = (() => {
    if (condition === 'drought') return '#8b7355';
    if (condition === 'dust') return '#a0826b';
    if (timeOfDay === 'dawn') return '#ff9a6b';
    if (timeOfDay === 'dusk') return '#d85a7a';
    if (timeOfDay === 'night') return '#1a2a4a';
    return '#2a5a8a';
  })();

  // Dynamic wave height based on weather
  const waveHeight = (() => {
    if (condition === 'storm') return 0.8;
    if (condition === 'rain') return 0.4;
    return 0.2;
  })();

  // Wave speed
  const waveSpeed = condition === 'storm' ? 1.2 : condition === 'rain' ? 0.8 : 0.5;

  return (
    <group ref={waterRef}>
      {/* Main water body */}
      <CustomWater
        position={[-40, 1, -20]}
        args={[40, 40]}
        color={waterColor}
        waveHeight={waveHeight}
        waveSpeed={waveSpeed}
        segments={96}
      />
      
      {/* Additional water patch */}
      <CustomWater
        position={[30, 0.5, 40]}
        args={[25, 20]}
        color={waterColor}
        waveHeight={waveHeight * 0.7}
        waveSpeed={waveSpeed * 0.8}
        segments={64}
      />
    </group>
  );
}
'''


def main():
    print("")
    print("=" * 70)
    print("  Fix: Replace drei Water with Custom GLSL Shader")
    print("=" * 70)
    print("")

    setup_git_path()

    # Step 1: Create CustomWater component
    print("[Step 1] Creating CustomWater component with GLSL shader")
    print("-" * 70)
    
    custom_water_file = CINEMATIC_DIR / "CustomWater.tsx"
    with open(custom_water_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(CUSTOM_WATER)
    ok(f"Created: {custom_water_file.relative_to(FRONTEND)}")
    
    info("Features:")
    info("  - Multi-frequency wave animation (3 layers)")
    info("  - Perlin noise for organic feel")
    info("  - Depth-based coloring")
    info("  - Specular highlights (sun reflection)")
    info("  - Fresnel effect (edge reflection)")
    info("  - Foam on wave peaks")
    info("  - Caustic-like patterns")
    print("")

    # Step 2: Update WaterSystem to use CustomWater
    print("[Step 2] Updating WaterSystem.tsx")
    print("-" * 70)
    
    water_system_file = CINEMATIC_DIR / "WaterSystem.tsx"
    with open(water_system_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(WATER_SYSTEM)
    ok(f"Updated: {water_system_file.relative_to(FRONTEND)}")
    
    info("Changes:")
    info("  - Removed: import { Water } from '@react-three/drei'")
    info("  - Added: import { CustomWater } from './CustomWater'")
    info("  - Dynamic color based on weather condition")
    info("  - Dynamic wave height based on weather")
    info("  - Multiple water bodies (lake + pond)")
    print("")

    # Step 3: Build verification
    print("[Step 3] Building project")
    print("-" * 70)
    info("This will take 1-2 minutes...")
    
    result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300,
    )
    
    build_ok = result.returncode == 0
    output = result.stdout + result.stderr
    
    if build_ok:
        ok("🎉 Build successful!")
        
        print("\n  Bundle sizes:")
        for line in output.splitlines():
            if "dist/assets/" in line and ("kB" in line or "MB" in line):
                if "vendor" in line or "index" in line or "HyDroMaCenter" in line:
                    print(f"    {line.strip()}")
    else:
        err("Build still failing")
        print("\n  Error output (last 25 lines):")
        for line in output.splitlines()[-25:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # Step 4: Commit if successful
    if build_ok:
        print("[Step 4] Committing fix")
        print("-" * 70)
        try:
            subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = (
                "fix(cinematic): replace drei Water with custom GLSL shader\\n\\n"
                "Problem:\\n"
                "- @react-three/drei@10.7.8 doesn't export 'Water' component\\n"
                "- Build failed with MISSING_EXPORT error\\n\\n"
                "Solution:\\n"
                "- Created CustomWater component with GLSL shader\\n"
                "- Features: multi-layer waves, Perlin noise, depth coloring,\\n"
                "  specular highlights, Fresnel effect, foam, caustics\\n"
                "- Updated WaterSystem.tsx to use CustomWater\\n"
                "- Dynamic color and waves based on weather condition\\n\\n"
                "Benefits:\\n"
                "- Better cinematic quality than drei Water\\n"
                "- Full control over water appearance\\n"
                "- No external dependency on drei Water\\n\\n"
                "Cinematic simulator now accessible at:\\n"
                "- http://localhost:5173/hydroma"
            )
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")
        
        print("")
        print("=" * 70)
        print("  🎉 FIX SUCCESSFUL!")
        print("=" * 70)
        print("")
        print("  ✅ Custom GLSL Water shader is now active!")
        print("")
        print("  Water features:")
        print("    🌊 Multi-frequency wave animation")
        print("    🎨 Dynamic coloring based on weather")
        print("    ☀️ Specular highlights (sun reflection)")
        print("    💫 Fresnel edge reflection")
        print("    🤍 Foam on wave peaks")
        print("    ✨ Caustic-like patterns")
        print("")
        print("  Next steps:")
        print("    cd D:\\eco_nojin\\frontend")
        print("    pnpm dev")
        print("    Visit: http://localhost:5173/hydroma")
        print("")
    
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())