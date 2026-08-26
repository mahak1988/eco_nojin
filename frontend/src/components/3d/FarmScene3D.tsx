import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sky } from '@react-three/drei';
import * as THREE from 'three';

interface FarmScene3DProps {
  showTerrain?: boolean;
  showCrops?: boolean;
  cropType?: string;
  growthStage?: number;
  ndvi?: number;
  herds?: Array<{ type: string; count: number }>;
}

const Tree = ({ position }: { position: [number, number, number] }) => {
  const ref = useRef<THREE.Group>(null);
  useFrame((state) => {
    if (ref.current) {
      // استفاده از state.clock به جای THREE.Clock
      ref.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.5 + position[0]) * 0.05;
    }
  });
  return (
    <group ref={ref} position={position}>
      <mesh position={[0, 1.5, 0]} castShadow>
        <cylinderGeometry args={[0.2, 0.3, 3, 8]} />
        <meshStandardMaterial color="#5c4033" roughness={0.9} />
      </mesh>
      <mesh position={[0, 3.5, 0]} castShadow>
        <coneGeometry args={[1.5, 3, 8]} />
        <meshStandardMaterial color="#2d5a27" roughness={0.8} />
      </mesh>
    </group>
  );
};

const Crop = ({ position, height, color }: { position: [number, number, number]; height: number; color: string }) => (
  <mesh position={[position[0], height / 2, position[2]]} castShadow>
    <coneGeometry args={[0.1, height, 6]} />
    <meshStandardMaterial color={color} />
  </mesh>
);

const Animal = ({ position, type }: { position: [number, number, number]; type: string }) => {
  const ref = useRef<THREE.Group>(null);
  const offset = useMemo(() => Math.random() * Math.PI * 2, []);
  
  useFrame((state) => {
    if (ref.current) {
      const t = state.clock.elapsedTime + offset;
      ref.current.position.x = position[0] + Math.sin(t * 0.3) * 2;
      ref.current.position.z = position[2] + Math.cos(t * 0.3) * 2;
      ref.current.rotation.y = Math.atan2(Math.cos(t * 0.3), -Math.sin(t * 0.3));
    }
  });

  const color = type === 'sheep' ? '#f0f0e8' : '#a0826d';
  return (
    <group ref={ref} position={position}>
      <mesh position={[0, 0.4, 0]} castShadow>
        <boxGeometry args={[0.5, 0.4, 1]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[0, 0.5, 0.4]} castShadow>
        <sphereGeometry args={[0.2, 8, 8]} />
        <meshStandardMaterial color={color} />
      </mesh>
    </group>
  );
};

export const FarmScene3D: React.FC<FarmScene3DProps> = ({
  showTerrain = true,
  showCrops = true,
  growthStage = 0.7,
  ndvi = 0.75,
  herds = [],
}) => {
  const treePositions: [number, number, number][] = [
    [-15, 0, -15], [15, 0, -15], [-15, 0, 15], [15, 0, 15],
    [-20, 0, 0], [20, 0, 0], [0, 0, -20], [0, 0, 20],
  ];

  const cropPositions = useMemo(() => {
    const positions: { pos: [number, number, number]; height: number }[] = [];
    for (let i = -10; i <= 10; i += 1.5) {
      for (let j = -10; j <= 10; j += 1.5) {
        if (Math.abs(i) > 2 || Math.abs(j) > 2) { // Avoid center
          positions.push({
            pos: [i + Math.random() * 0.5, 0, j + Math.random() * 0.5],
            height: 0.3 + growthStage * 0.7 + Math.random() * 0.2,
          });
        }
      }
    }
    return positions;
  }, [growthStage]);

  const cropColor = ndvi > 0.6 ? '#84cc16' : ndvi > 0.4 ? '#eab308' : '#d4a574';

  return (
    <div style={{ width: '100%', height: 500, borderRadius: 'var(--radius-lg)', overflow: 'hidden', background: '#1a1a2e' }}>
      <Canvas shadows camera={{ position: [25, 20, 25], fov: 50 }}>
        <Sky sunPosition={[100, 50, 100]} />
        <ambientLight intensity={0.6} />
        <directionalLight position={[30, 30, 30]} intensity={1.2} castShadow shadow-mapSize={[2048, 2048]} />

        {showTerrain && (
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
            <planeGeometry args={[60, 60]} />
            <meshStandardMaterial color="#8b7355" roughness={0.95} />
          </mesh>
        )}

        {treePositions.map((pos, i) => <Tree key={`tree-${i}`} position={pos} />)}

        {showCrops && cropPositions.map((c, i) => (
          <Crop key={`crop-${i}`} position={c.pos} height={c.height} color={cropColor} />
        ))}

        {herds.map((herd, hIndex) => 
          Array.from({ length: Math.min(herd.count, 10) }).map((_, i) => (
            <Animal
              key={`animal-${hIndex}-${i}`}
              position={[
                (Math.random() - 0.5) * 20,
                0,
                (Math.random() - 0.5) * 20,
              ]}
              type={herd.type}
            />
          ))
        )}

        <OrbitControls enablePan enableZoom enableRotate maxPolarAngle={Math.PI / 2.1} />
      </Canvas>
    </div>
  );
};
