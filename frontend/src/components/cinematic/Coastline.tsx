import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight, LAKE_LEVEL } from '../../utils/terrainHeight';

/** Sandy shore ring around the lake. */
export function Coastline() {
  const ring = useMemo(() => {
    const pts: { x: number; z: number; y: number; rot: number }[] = [];
    for (let i = 0; i < 24; i++) {
      const a = (i / 24) * Math.PI * 2;
      const r = 56 + Math.sin(i * 3.7) * 4;
      const x = Math.cos(a) * r;
      const z = Math.sin(a) * r;
      pts.push({ x, z, y: Math.max(getTerrainHeight(x, z), LAKE_LEVEL + 0.25), rot: -a });
    }
    return pts;
  }, []);

  return (
    <group>
      {ring.map((p, i) => (
        <mesh key={i} position={[p.x, p.y, p.z]} rotation={[-Math.PI / 2, 0, p.rot]} receiveShadow>
          <planeGeometry args={[16, 7]} />
          <meshStandardMaterial color="#e8d5a6" roughness={0.95} />
        </mesh>
      ))}
    </group>
  );
}
