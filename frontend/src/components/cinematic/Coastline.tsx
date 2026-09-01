import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

/**
 * Continuous beach: 56 overlapping sand quads hugging the terrain,
 * oriented tangentially (no more scattered white rectangles).
 */
export function Coastline() {
  const patches = useMemo(() => {
    const list: { x: number; z: number; y: number; yaw: number; s: number }[] = [];
    const N = 56;
    for (let i = 0; i < N; i++) {
      const a = (i / N) * Math.PI * 2;
      const r = 58 + Math.sin(i * 2.7) * 3;
      const x = Math.cos(a) * r;
      const z = Math.sin(a) * r;
      const y = getTerrainHeight(x, z) + 0.06;
      list.push({ x, z, y, yaw: -a + Math.PI / 2, s: 0.9 + Math.sin(i * 1.3) * 0.15 });
    }
    return list;
  }, []);

  return (
    <group>
      {patches.map((p, i) => (
        <group key={i} position={[p.x, p.y, p.z]} rotation={[0, p.yaw, 0]} scale={p.s}>
          <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
            <planeGeometry args={[11, 9]} />
            <meshStandardMaterial color="#e6d3a3" roughness={0.95} />
          </mesh>
        </group>
      ))}
    </group>
  );
}
