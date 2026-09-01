import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Realistic flood water spreading across terrain
export function FloodSimulation() {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  
  const geometry = useMemo(() => new THREE.PlaneGeometry(200, 200, 64, 64), []);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uColor: { value: new THREE.Color('#3d6098') },
    uFloodLevel: { value: 0.7 },
  }), []);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
  });

  return (
    <mesh ref={meshRef} geometry={geometry} rotation={[-Math.PI / 2, 0, 0]} position={[0, 1.5, 0]}>
      <shaderMaterial
        ref={materialRef}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        vertexShader={`
          uniform float uTime;
          uniform float uFloodLevel;
          varying vec2 vUv;
          varying float vHeight;
          void main() {
            vUv = uv;
            vec3 p = position;
            float wave = sin(p.x * 0.1 + uTime * 2.0) * 0.3 + cos(p.y * 0.15 + uTime * 1.5) * 0.2;
            p.z = wave * uFloodLevel;
            vHeight = p.z;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
          }
        `}
        fragmentShader={`
          uniform vec3 uColor;
          uniform float uTime;
          varying vec2 vUv;
          varying float vHeight;
          void main() {
            float foam = smoothstep(0.3, 0.5, vHeight);
            vec3 color = mix(uColor, vec3(0.9, 0.95, 1.0), foam * 0.5);
            float alpha = 0.7 + foam * 0.2;
            gl_FragColor = vec4(color, alpha);
          }
        `}
      />
    </mesh>
  );
}
