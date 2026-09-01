import { useRef, useMemo } from 'react';
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
