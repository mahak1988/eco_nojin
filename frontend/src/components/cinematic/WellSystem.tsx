import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

export function WellSystem() {
  const h = useMemo(() => getTerrainHeight(35, -35), []);
  return (
    <group position={[35, h, -35]}>
      <mesh castShadow><cylinderGeometry args={[1.5, 1.8, 1.5, 16, 1, true]} /><meshStandardMaterial color="#8b7355" roughness={0.95} side={THREE.DoubleSide} /></mesh>
      <mesh position={[0, 0.8, 0]} castShadow><torusGeometry args={[1.6, 0.15, 8, 24]} /><meshStandardMaterial color="#6b5d47" /></mesh>
      <mesh position={[0, -0.6, 0]}><cylinderGeometry args={[1.4, 1.4, 0.1, 24]} /><meshStandardMaterial color="#2a5a8a" metalness={0.3} roughness={0.1} /></mesh>
      <mesh position={[0, 2, 0]} castShadow><boxGeometry args={[0.2, 3, 0.2]} /><meshStandardMaterial color="#5a3a20" /></mesh>
      <mesh position={[0, 3.5, 0]} castShadow><boxGeometry args={[3, 0.2, 0.2]} /><meshStandardMaterial color="#5a3a20" /></mesh>
    </group>
  );
}
