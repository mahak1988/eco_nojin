import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getTerrainHeight } from '../../utils/terrainHeight';

export function InsectsSystem() {
  const groupRef = useRef<THREE.Group>(null);

  const insects = useMemo(() => {
    const list = [];
    const mk = (color: string, size: number, n: number, hMin: number, hMax: number, speed: number) => {
      for (let i = 0; i < n; i++) {
        const x = (Math.random() - 0.5) * 90;
        const z = (Math.random() - 0.5) * 90;
        const base = getTerrainHeight(x, z);
        list.push({ color, size, x, z, base, hOff: hMin + Math.random() * (hMax - hMin), phase: Math.random() * 6.28, speed });
      }
    };
    mk('#ffcc00', 0.15, 20, 1, 3, 0.8);   // bees
    mk('#d63031', 0.12, 15, 0.4, 1.2, 0.3); // ladybugs
    mk('#6c5b3c', 0.2, 8, 1.5, 4, 1.2);  // locusts
    return list;
  }, []);

  useFrame((state) => {
    if (!groupRef.current) return;
    const t = state.clock.elapsedTime;
    groupRef.current.children.forEach((m, i) => {
      const ins = insects[i];
      const tt = t * ins.speed + ins.phase;
      m.position.set(
        ins.x + Math.sin(tt) * 4,
        ins.base + ins.hOff + Math.sin(tt * 2) * 0.4,
        ins.z + Math.cos(tt * 0.7) * 4
      );
      m.rotation.y = tt;
    });
  });

  return (
    <group ref={groupRef}>
      {insects.map((ins, i) => (
        <mesh key={i}><sphereGeometry args={[ins.size, 6, 5]} /><meshStandardMaterial color={ins.color} /></mesh>
      ))}
    </group>
  );
}
