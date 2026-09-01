import { useMemo } from 'react';
import * as THREE from 'three';

// Check dams, terraces, gabion walls - watershed engineering
function CheckDam({ position, width = 8 }: { position: [number, number, number]; width?: number }) {
  return (
    <group position={position}>
      {/* Gabion structure */}
      <mesh castShadow receiveShadow>
        <boxGeometry args={[width, 1.5, 1.5]} />
        <meshStandardMaterial color="#7d7468" roughness={1.0} />
      </mesh>
      {/* Rock texture overlay */}
      {Array.from({ length: 8 }).map((_, i) => (
        <mesh key={i} position={[
          (i - 3.5) * (width / 8),
          Math.random() * 0.5 + 0.3,
          Math.random() * 0.5 - 0.25
        ]} castShadow>
          <dodecahedronGeometry args={[0.3 + Math.random() * 0.2, 0]} />
          <meshStandardMaterial color="#5d5448" roughness={1.0} />
        </mesh>
      ))}
      {/* Small pool behind dam */}
      <mesh position={[0, 0.1, -2]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[width, 4]} />
        <meshStandardMaterial color="#2a5a8a" transparent opacity={0.7} />
      </mesh>
    </group>
  );
}

function Terrace({ position, level }: { position: [number, number, number]; level: number }) {
  return (
    <group position={position}>
      <mesh castShadow receiveShadow>
        <boxGeometry args={[30, 0.5, 8]} />
        <meshStandardMaterial color="#6b5d3d" roughness={0.95} />
      </mesh>
      {/* Retaining wall */}
      <mesh position={[0, 0.5, -4.25]} castShadow>
        <boxGeometry args={[30, 1, 0.5]} />
        <meshStandardMaterial color="#8b7355" roughness={1.0} />
      </mesh>
      {/* Crops on terrace */}
      {Array.from({ length: 10 }).map((_, i) => (
        <mesh key={i} position={[(i - 4.5) * 2.8, 0.7, 0]} castShadow>
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
      {/* Series of check dams */}
      <CheckDam position={[-50, 0, 30]} width={10} />
      <CheckDam position={[-35, 0, 45]} width={8} />
      <CheckDam position={[-20, 0, 55]} width={6} />
      
      {/* Terraced hillside */}
      <Terrace position={[50, 0, 50]} level={0} />
      <Terrace position={[50, 1, 40]} level={1} />
      <Terrace position={[50, 2, 30]} level={2} />
      
      {/* Diversion channel */}
      <mesh position={[0, 0.05, 60]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[40, 3]} />
        <meshStandardMaterial color="#3d6098" transparent opacity={0.8} />
      </mesh>
    </group>
  );
}
