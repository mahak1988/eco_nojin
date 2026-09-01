import { useRef, useMemo } from 'react';
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
