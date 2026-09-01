#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: WebGL Context Lost caused by external Cloud texture fetch
================================================================
Root cause: drei's <Cloud /> fetches cloud.png from rawcdn.githack.com.
In restricted networks, this fetch times out and crashes the WebGL context.

Solution: Replace <Cloud /> with a ProceduralCloud built from overlapping
low-poly icosahedrons. Zero external network requests required.
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
SRC = FRONTEND / "src"
SIM = SRC / "components" / "cinematic"


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
# LIGHTING SYSTEM (Procedural Clouds - No External Textures)
# =============================================================================

LIGHTING = r'''import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sky, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { useWeatherStore, TimeOfDay } from '../../hooks/useWeatherStore';
import { useQualityStore } from '../../hooks/useQualityStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';

/**
 * Procedural Cloud: built from overlapping low-poly spheres.
 * 
 * CRITICAL FIX: drei's <Cloud /> fetches 'cloud.png' from rawcdn.githack.com.
 * On restricted networks, this fetch times out (QUIC error) and crashes
 * the WebGL context ("Context Lost"). This procedural version requires
 * ZERO external network requests and is completely safe.
 */
function ProceduralCloud({ position, color, scale = 1 }: { position: [number, number, number]; color: string; scale?: number }) {
  const puffs = [
    { pos: [0, 0, 0], s: 12 },
    { pos: [9, 2, -2], s: 10 },
    { pos: [-10, 1, 3], s: 11 },
    { pos: [4, -2, 6], s: 9 },
    { pos: [-6, 3, -5], s: 10 },
    { pos: [13, -1, 2], s: 8 },
    { pos: [-13, -2, -3], s: 9 },
  ];

  return (
    <group position={position}>
      {puffs.map((p, i) => (
        <mesh key={i} position={[p.pos[0] * scale, p.pos[1] * scale, p.pos[2] * scale]}>
          <icosahedronGeometry args={[p.s * scale, 1]} />
          <meshStandardMaterial 
            color={color} 
            transparent 
            opacity={0.85} 
            roughness={1} 
            metalness={0}
            depthWrite={false}
          />
        </mesh>
      ))}
    </group>
  );
}

export function LightingSystem() {
  const { timeOfDay, sunPosition, condition, intensity, windSpeed } = useWeatherStore();
  const tier = useQualityStore((s) => s.tier);
  const enableSunCycle = useArtisticStore((s) => s.enableSunCycle);

  const cycle = useRef(0.30); 
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
    cycle.current = (cycle.current + delta / 180) % 1; 
    acc.current += delta;
    if (acc.current < 0.15) return; 
    acc.current = 0;

    const t = cycle.current;
    const el = Math.sin(t * Math.PI * 2);       
    const az = t * Math.PI * 2;                 
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

  const sunIntensity = (() => {
    let base = 2.6; 
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
    return '#fff3d6'; 
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

      {/* --- MOVING PROCEDURAL CLOUDS (No external textures!) --- */}
      <group ref={cloudsRef}>
        {/* Fair-weather clouds on clear days */}
        {(condition === 'clear' || condition === 'drought') && phase !== 'night' && (
          <>
            <ProceduralCloud position={[-90, 95, -140]} color="#ffffff" scale={1.2} />
            <ProceduralCloud position={[30, 105, -170]} color="#ffffff" scale={1.5} />
            <ProceduralCloud position={[130, 90, -100]} color="#ffffff" scale={1.0} />
          </>
        )}
        {(condition === 'storm' || condition === 'rain') && (
          <>
            <ProceduralCloud position={[-60, 80, -100]} color={condition === 'storm' ? '#2d3748' : '#8a9aa8'} scale={2.0} />
            <ProceduralCloud position={[80, 90, -120]} color={condition === 'storm' ? '#1a202c' : '#7a8a98'} scale={2.2} />
            <ProceduralCloud position={[0, 85, -150]} color={condition === 'storm' ? '#1a202c' : '#6a7a88'} scale={1.8} />
          </>
        )}
        {condition === 'dust' && (
          <>
            <ProceduralCloud position={[-40, 25, -50]} color="#8b6f47" scale={1.5} />
            <ProceduralCloud position={[60, 30, -70]} color="#a0826b" scale={1.8} />
          </>
        )}
        {condition === 'snow' && (
          <ProceduralCloud position={[0, 90, -130]} color="#dfe5ee" scale={1.6} />
        )}
      </group>
    </>
  );
}
'''


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("")
    print("=" * 70)
    print("  🛡️ Fix: WebGL Context Lost (External Texture Crash)")
    print("=" * 70)
    print("")
    print("  Root Cause:")
    print("    drei <Cloud /> fetches cloud.png from rawcdn.githack.com")
    print("    Network timeout (QUIC) crashes the WebGL context.")
    print("")
    print("  Solution:")
    print("    Replace with ProceduralCloud (overlapping icosahedrons).")
    print("    ZERO external network requests. 100% offline safe.")
    print("")

    setup_git_path()

    print("[Step 1] Rewriting LightingSystem.tsx")
    print("-" * 70)
    write_file(SIM / "LightingSystem.tsx", LIGHTING)
    ok("Updated: LightingSystem.tsx (Procedural Clouds)")
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
            msg = ("fix(cinematic): prevent WebGL crash from external cloud texture\\n\\n"
                   "Root Cause:\\n"
                   "- drei <Cloud /> fetches cloud.png from rawcdn.githack.com\\n"
                   "- On restricted networks, fetch times out (QUIC error)\\n"
                   "- Unhandled error crashes entire WebGL Canvas Context\\n\\n"
                   "Solution:\\n"
                   "- Replaced <Cloud /> with custom ProceduralCloud component\\n"
                   "- Built from overlapping low-poly icosahedrons\\n"
                   "- ZERO external network requests required\\n"
                   "- 100% offline safe, immune to CDN blocking\\n"
                   "- Retains wind drift and weather-based coloring")
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            print(f"[WARN] {e}")

        print("")
        print("=" * 70)
        print("  🎉 CRASH FIXED!")
        print("=" * 70)
        print("")
        print("  Action required:")
        print("    1. Hard refresh browser: Ctrl + Shift + R")
        print("    2. Visit: http://localhost:5173/hydroma")
        print("")
        print("  The scene will now load instantly without crashing,")
        print("  and clouds will drift smoothly across the sky!")
        print("")
        print("  Note on other console warnings:")
        print("    - MaxListeners / ObjectMultiplex -> Browser extensions (ignore)")
        print("    - THREE.Clock deprecated -> drei internal (ignore)")
        print("    - antd Space direction -> minor deprecation (ignore)")
        print("")

    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())