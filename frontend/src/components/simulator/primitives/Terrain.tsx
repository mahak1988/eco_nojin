import { useMemo, useRef } from 'react';
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
