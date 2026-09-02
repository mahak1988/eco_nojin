import { useMemo, useRef } from 'react';
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
