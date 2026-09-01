import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

function Animal({ color, size = 1 }: { color: string; size?: number }) {
  return (
    <group scale={size}>
      <mesh position={[0, 0.8, 0]} castShadow><boxGeometry args={[1.5, 0.8, 0.7]} /><meshStandardMaterial color={color} /></mesh>
      <mesh position={[0.8, 1.1, 0]} castShadow><boxGeometry args={[0.5, 0.5, 0.5]} /><meshStandardMaterial color={color} /></mesh>
      {[[-0.5, 0.4, -0.2], [-0.5, 0.4, 0.2], [0.5, 0.4, -0.2], [0.5, 0.4, 0.2]].map((p, i) => (
        <mesh key={i} position={p as [number, number, number]} castShadow><boxGeometry args={[0.15, 0.8, 0.15]} /><meshStandardMaterial color="#2d3436" /></mesh>
      ))}
    </group>
  );
}

export function DomesticAnimals() {
  const groupRef = useRef<THREE.Group>(null);

  const animals = useMemo(() => {
    const list = [];
    const mk = (type: string, color: string, size: number, x: number, z: number, speed: number) =>
      list.push({ type, color, size, x, z, h: getTerrainHeight(x, z), speed, phase: Math.random() * Math.PI * 2 });
    for (let i = 0; i < 5; i++) mk('cow', i % 2 ? '#8b4513' : '#f5f0e8', 1.2, 25 + Math.random() * 25, -15 + Math.random() * 30, 0.05 + Math.random() * 0.05);
    for (let i = 0; i < 8; i++) mk('sheep', '#f5f5dc', 0.8, -30 + Math.random() * 22, 12 + Math.random() * 25, 0.08 + Math.random() * 0.05);
    for (let i = 0; i < 3; i++) mk('horse', '#6b3e2a', 1.5, 40 + Math.random() * 15, 25 + Math.random() * 15, 0.1 + Math.random() * 0.1);
    return list;
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((g, i) => {
      const a = animals[i];
      const tt = t * a.speed + a.phase;
      const x = a.x + Math.sin(tt) * 6;
      const z = a.z + Math.cos(tt * 0.8) * 6;
      g.position.set(x, getTerrainHeight(x, z), z);
      g.rotation.y = tt + Math.PI / 2;
    });
  });

  return (
    <group ref={groupRef}>
      {animals.map((a, i) => <group key={i}><Animal color={a.color} size={a.size} /></group>)}
    </group>
  );
}
