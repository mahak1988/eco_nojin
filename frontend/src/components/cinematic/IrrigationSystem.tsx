import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

function Sprinkler({ position }: { position: [number, number, number] }) {
  const sprayRef = useRef<THREE.Points>(null);
  const count = 250;
  const positions = useMemo(() => new Float32Array(count * 3), []);
  const velocities = useMemo(() => {
    const v = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const a = (i / count) * Math.PI * 2;
      v[i * 3] = Math.cos(a) * 0.3; v[i * 3 + 1] = 0.4 + Math.random() * 0.2; v[i * 3 + 2] = Math.sin(a) * 0.3;
    }
    return v;
  }, []);

  useFrame((state) => {
    if (!sprayRef.current) return;
    const attr = sprayRef.current.geometry.attributes.position as THREE.BufferAttribute;
    const arr = attr.array as Float32Array;
    const t = state.clock.elapsedTime;
    for (let i = 0; i < count; i++) {
      arr[i * 3] += velocities[i * 3] * 0.15;
      arr[i * 3 + 1] += velocities[i * 3 + 1] * 0.1 - 0.015;
      arr[i * 3 + 2] += velocities[i * 3 + 2] * 0.15;
      if (arr[i * 3 + 1] < 0) {
        const a = (i / count) * Math.PI * 2 + t * 2;
        const s = 0.3 + Math.random() * 0.3;
        arr[i * 3] = 0; arr[i * 3 + 1] = 2; arr[i * 3 + 2] = 0;
        velocities[i * 3] = Math.cos(a) * s; velocities[i * 3 + 2] = Math.sin(a) * s;
      }
    }
    attr.needsUpdate = true;
  });

  return (
    <group position={position}>
      <mesh position={[0, 1, 0]} castShadow><cylinderGeometry args={[0.08, 0.1, 2, 8]} /><meshStandardMaterial color="#2c3e50" metalness={0.8} /></mesh>
      <points ref={sprayRef} position={[0, 2, 0]}>
        <bufferGeometry><bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} /></bufferGeometry>
        <pointsMaterial size={0.1} color="#4fa3d1" transparent opacity={0.7} depthWrite={false} blending={THREE.AdditiveBlending} />
      </points>
    </group>
  );
}

export function IrrigationSystem() {
  const spots = useMemo(() => {
    const s: [number, number, number][] = [];
    [[-20, -20], [0, -20], [20, -20], [-20, 5], [0, 5], [20, 5]].forEach(([x, z]) => {
      s.push([x, getTerrainHeight(x, z), z]);
    });
    return s;
  }, []);

  return (
    <group>
      {spots.map((p, i) => <Sprinkler key={i} position={p} />)}
    </group>
  );
}
