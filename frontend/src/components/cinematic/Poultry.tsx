import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

export function Poultry() {
  const groupRef = useRef<THREE.Group>(null);

  const birds = useMemo(() => {
    const list = [];
    for (let i = 0; i < 12; i++) {
      const x = -8 + Math.random() * 18, z = 18 + Math.random() * 14;
      list.push({ color: i % 3 === 0 ? '#8b4513' : i % 3 === 1 ? '#ffffff' : '#d4a574', size: 0.4, x, z, h: getTerrainHeight(x, z), phase: Math.random() * 6.28, speed: 0.2 + Math.random() * 0.2 });
    }
    for (let i = 0; i < 5; i++) {
      const x = -20 + Math.random() * 10, z = -8 + Math.random() * 8;
      list.push({ color: '#f4d03f', size: 0.35, x, z, h: getTerrainHeight(x, z), phase: Math.random() * 6.28, speed: 0.15 + Math.random() * 0.15 });
    }
    return list;
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((g, i) => {
      const b = birds[i];
      const x = b.x + Math.sin(t * b.speed + b.phase) * 3;
      const z = b.z + Math.cos(t * b.speed * 0.8 + b.phase) * 3;
      g.position.set(x, getTerrainHeight(x, z) + Math.abs(Math.sin(t * 4 + b.phase)) * 0.15, z);
      g.rotation.y = t * b.speed;
    });
  });

  return (
    <group ref={groupRef}>
      {birds.map((b, i) => (
        <group key={i} scale={b.size}>
          <mesh position={[0, 0.4, 0]} castShadow><sphereGeometry args={[0.5, 8, 6]} /><meshStandardMaterial color={b.color} /></mesh>
          <mesh position={[0.3, 0.7, 0]} castShadow><sphereGeometry args={[0.25, 8, 6]} /><meshStandardMaterial color={b.color} /></mesh>
          <mesh position={[0.55, 0.7, 0]}><coneGeometry args={[0.08, 0.15, 4]} /><meshStandardMaterial color="#ff6b00" /></mesh>
        </group>
      ))}
    </group>
  );
}
