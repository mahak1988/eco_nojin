import { useMemo } from 'react';
import * as THREE from 'three';

// Plowing trails - visible furrows in the field
export function PlowingTrails() {
  const furrows = useMemo(() => {
    const arr = [];
    for (let i = 0; i < 15; i++) {
      arr.push(i * 3 - 21);
    }
    return arr;
  }, []);

  return (
    <group position={[0, 0.05, 50]}>
      {/* Furrow lines */}
      {furrows.map((z, i) => (
        <mesh key={i} position={[0, 0, z]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[60, 0.3]} />
          <meshStandardMaterial color="#4a3520" roughness={1.0} />
        </mesh>
      ))}
      {/* Raised soil between furrows */}
      {furrows.map((z, i) => (
        <mesh key={`ridge-${i}`} position={[0, 0.1, z + 1.5]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[60, 1.5]} />
          <meshStandardMaterial color="#6b4423" roughness={0.95} />
        </mesh>
      ))}
      {/* Tractor */}
      <group position={[20, 0, furrows[7]]}>
        <mesh position={[0, 1, 0]} castShadow>
          <boxGeometry args={[2, 1.5, 1.2]} />
          <meshStandardMaterial color="#d63031" />
        </mesh>
        <mesh position={[-1.2, 1.2, 0]} castShadow>
          <boxGeometry args={[0.8, 1, 1]} />
          <meshStandardMaterial color="#2d3436" />
        </mesh>
        {/* Wheels */}
        {[[-0.8, 0.4, 0.7], [-0.8, 0.4, -0.7], [0.8, 0.6, 0.7], [0.8, 0.6, -0.7]].map((pos, i) => (
          <mesh key={i} position={pos as [number, number, number]} rotation={[Math.PI / 2, 0, 0]} castShadow>
            <cylinderGeometry args={[i < 2 ? 0.4 : 0.6, i < 2 ? 0.4 : 0.6, 0.3, 16]} />
            <meshStandardMaterial color="#1a1a1a" />
          </mesh>
        ))}
      </group>
    </group>
  );
}
