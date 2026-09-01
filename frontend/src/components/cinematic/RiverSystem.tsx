import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { LAKE_LEVEL } from '../../utils/terrainHeight';

/** Inflow stream feeding the lake, kept inside the flat basin. */
export function RiverSystem() {
  const matRef = useRef<THREE.ShaderMaterial>(null);

  useFrame((state) => {
    if (matRef.current) matRef.current.uniforms.uTime.value = state.clock.elapsedTime;
  });

  return (
    <mesh position={[55, LAKE_LEVEL + 0.15, -20]} rotation={[-Math.PI / 2, 0, -0.4]}>
      <planeGeometry args={[90, 5, 32, 4]} />
      <shaderMaterial
        ref={matRef}
        transparent
        uniforms={{ uTime: { value: 0 } }}
        vertexShader={`
          varying vec2 vUv;
          void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
        `}
        fragmentShader={`
          uniform float uTime;
          varying vec2 vUv;
          void main() {
            float flow = fract(vUv.x * 6.0 - uTime * 0.6);
            vec3 color = mix(vec3(0.12, 0.32, 0.52), vec3(0.3, 0.6, 0.8), flow);
            float edge = smoothstep(0.0, 0.15, vUv.y) * smoothstep(1.0, 0.85, vUv.y);
            gl_FragColor = vec4(color, 0.85 * edge);
          }
        `}
      />
    </mesh>
  );
}
