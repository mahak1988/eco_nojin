import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

export function PlowingTrails() {
  const base = useMemo(() => getTerrainHeight(0, 45), []);
  const furrows = useMemo(() => Array.from({ length: 12 }, (_, i) => i * 3 - 16), []);

  return (
    <group position={[0, base + 0.05, 45]}>
      {furrows.map((z, i) => (
        <mesh key={i} position={[0, 0, z]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[50, 0.35]} />
          <meshStandardMaterial color="#4a3520" roughness={1} />
        </mesh>
      ))}
      {/* Tractor */}
      <group position={[15, 0.1, 0]}>
        <mesh position={[0, 1, 0]} castShadow><boxGeometry args={[2, 1.5, 1.2]} /><meshStandardMaterial color="#d63031" /></mesh>
        <mesh position={[-1.2, 1.2, 0]} castShadow><boxGeometry args={[0.8, 1, 1]} /><meshStandardMaterial color="#2d3436" /></mesh>
        {[[-0.8, 0.4, 0.7], [-0.8, 0.4, -0.7], [0.8, 0.6, 0.7], [0.8, 0.6, -0.7]].map((p, i) => (
          <mesh key={i} position={p as [number, number, number]} rotation={[Math.PI / 2, 0, 0]} castShadow>
            <cylinderGeometry args={[i < 2 ? 0.4 : 0.6, i < 2 ? 0.4 : 0.6, 0.3, 16]} />
            <meshStandardMaterial color="#1a1a1a" />
          </mesh>
        ))}
      </group>
    </group>
  );
}
