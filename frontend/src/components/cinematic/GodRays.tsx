import { useMemo } from 'react';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

/** Subtle vertical light shafts over the farm valley (not a floating fan!). */
export function GodRays() {
  const shafts = useMemo(() => {
    const arr = [];
    for (let i = 0; i < 9; i++) {
      const angle = (i / 9) * Math.PI * 2;
      const r = 18 + (i % 3) * 9;
      const x = Math.cos(angle) * r;
      const z = Math.sin(angle) * r;
      const h = getTerrainHeight(x, z);
      arr.push({ x, z, y: h + 18, tilt: (i % 2 === 0 ? 1 : -1) * 0.06, radius: 1.2 + (i % 3) * 0.7 });
    }
    return arr;
  }, []);

  return (
    <group>
      {shafts.map((s, i) => (
        <mesh key={i} position={[s.x, s.y, s.z]} rotation={[s.tilt, 0, s.tilt]}>
          <cylinderGeometry args={[s.radius * 0.4, s.radius, 36, 8, 1, true]} />
          <meshBasicMaterial
            color="#fff4c8"
            transparent
            opacity={0.055}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
    </group>
  );
}
