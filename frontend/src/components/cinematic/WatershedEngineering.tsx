import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

function CheckDam({ x, z, width = 8 }: { x: number; z: number; width?: number }) {
  const h = useMemo(() => getTerrainHeight(x, z), [x, z]);
  return (
    <group position={[x, h + 0.4, z]}>
      <mesh castShadow receiveShadow><boxGeometry args={[width, 1.5, 1.5]} /><meshStandardMaterial color="#7d7468" roughness={1} /></mesh>
      <mesh position={[0, 0.1, -2.5]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width, 4]} />
        <meshStandardMaterial color="#2a5a8a" transparent opacity={0.7} />
      </mesh>
    </group>
  );
}

function Terrace({ x, z, level }: { x: number; z: number; level: number }) {
  const h = useMemo(() => getTerrainHeight(x, z), [x, z]);
  return (
    <group position={[x, h + level * 0.8, z]}>
      <mesh castShadow receiveShadow><boxGeometry args={[26, 0.5, 7]} /><meshStandardMaterial color="#6b5d3d" roughness={0.95} /></mesh>
      <mesh position={[0, 0.5, -3.7]} castShadow><boxGeometry args={[26, 1, 0.5]} /><meshStandardMaterial color="#8b7355" /></mesh>
      {Array.from({ length: 8 }).map((_, i) => (
        <mesh key={i} position={[(i - 3.5) * 3, 0.8, 0]} castShadow>
          <coneGeometry args={[0.3, 1.2, 6]} />
          <meshStandardMaterial color={level % 2 === 0 ? '#6ba368' : '#a8c686'} />
        </mesh>
      ))}
    </group>
  );
}

export function WatershedEngineering() {
  return (
    <group>
      <CheckDam x={-45} z={30} width={10} />
      <CheckDam x={-32} z={42} width={8} />
      <CheckDam x={-20} z={52} width={6} />
      <Terrace x={48} z={48} level={0} />
      <Terrace x={48} z={39} level={1} />
      <Terrace x={48} z={30} level={2} />
    </group>
  );
}
