import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export function Fireflies() {
  const count = 200;
  const meshRef = useRef<THREE.Points>(null);
  const offsets = useMemo(() => new Float32Array(count).map(() => Math.random() * Math.PI * 2), []);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.sqrt(Math.random()) * 60;
      pos[i * 3] = Math.cos(angle) * radius;
      pos[i * 3 + 1] = 1 + Math.random() * 8;
      pos[i * 3 + 2] = Math.sin(angle) * radius;
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (!meshRef.current) return;
    const posAttr = meshRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = posAttr.array as Float32Array;
    const t = state.clock.elapsedTime;
    for (let i = 0; i < count; i++) {
      const off = offsets[i];
      arr[i * 3] += Math.sin(t * 0.8 + off) * 0.03;
      arr[i * 3 + 1] += Math.cos(t * 1.2 + off) * 0.02;
      arr[i * 3 + 2] += Math.sin(t * 0.6 + off * 2) * 0.03;
    }
    posAttr.needsUpdate = true;
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial
        size={0.4}
        color="#ffe66d"
        transparent
        opacity={0.9}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  );
}
