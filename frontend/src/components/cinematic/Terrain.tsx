import { useRef, useMemo, useEffect } from 'react';
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
