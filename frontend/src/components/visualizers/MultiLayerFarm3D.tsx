import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sky } from '@react-three/drei';
import * as THREE from 'three';

interface MultiLayerFarm3DProps {
  showCanopy?: boolean;
  showSubCanopy?: boolean;
  showGround?: boolean;
  showAnimals?: boolean;
  growthStage?: number; // 0-1
}

/**
 * درختان لایه بالایی (Canopy)
 */
const CanopyTree: React.FC<{ position: [number, number, number]; species: string }> = ({
  position,
  species,
}) => {
  const groupRef = useRef<THREE.Group>(null);
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.z = Math.sin(state.clock.elapsedTime + position[0]) * 0.02;
    }
  });

  const speciesData: Record<string, { trunk: string; leaves: string; height: number }> = {
    walnut: { trunk: '#654321', leaves: '#2d5016', height: 8 },
    olive: { trunk: '#8b7355', leaves: '#4a6741', height: 6 },
    pistachio: { trunk: '#a0826d', leaves: '#556b2f', height: 5 },
  };
  const data = speciesData[species] || speciesData.walnut;

  return (
    <group ref={groupRef} position={position}>
      <mesh position={[0, data.height / 2, 0]} castShadow>
        <cylinderGeometry args={[0.3, 0.5, data.height, 8]} />
        <meshStandardMaterial color={data.trunk} />
      </mesh>
      <mesh position={[0, data.height, 0]} castShadow>
        <sphereGeometry args={[2.5, 12, 12]} />
        <meshStandardMaterial color={data.leaves} roughness={0.8} />
      </mesh>
    </group>
  );
};

/**
 * بوته‌ها و درختچه‌های لایه میانی (Sub-Canopy)
 */
const SubCanopyBush: React.FC<{ position: [number, number, number] }> = ({ position }) => {
  return (
    <group position={position}>
      <mesh position={[0, 1, 0]} castShadow>
        <sphereGeometry args={[0.8, 8, 8]} />
        <meshStandardMaterial color="#6b8e4e" />
      </mesh>
      {/* میوه‌ها */}
      {Array.from({ length: 5 }).map((_, i) => (
        <mesh
          key={i}
          position={[
            Math.cos((i / 5) * Math.PI * 2) * 0.6,
            0.8 + Math.sin(i) * 0.3,
            Math.sin((i / 5) * Math.PI * 2) * 0.6,
          ]}
        >
          <sphereGeometry args={[0.1, 6, 6]} />
          <meshStandardMaterial color="#dc2626" />
        </mesh>
      ))}
    </group>
  );
};

/**
 * گیاهان زمینی (Ground Layer)
 */
const GroundCrop: React.FC<{ position: [number, number, number]; type: string }> = ({
  position,
  type,
}) => {
  const colors: Record<string, string> = {
    clover: '#22c55e',
    alfalfa: '#16a34a',
    mint: '#4ade80',
    saffron: '#a855f7',
  };
  return (
    <mesh position={position} castShadow>
      <coneGeometry args={[0.15, 0.5, 6]} />
      <meshStandardMaterial color={colors[type] || colors.clover} />
    </mesh>
  );
};

/**
 * دام‌های در حال چرا
 */
const GrazingAnimal: React.FC<{ position: [number, number, number]; type: string }> = ({
  position,
  type,
}) => {
  const ref = useRef<THREE.Group>(null);
  const offset = useRef(Math.random() * Math.PI * 2);
  
  useFrame((state) => {
    if (ref.current) {
      const t = state.clock.elapsedTime + offset.current;
      ref.current.position.x = position[0] + Math.sin(t * 0.2) * 2;
      ref.current.position.z = position[2] + Math.cos(t * 0.2) * 2;
      ref.current.rotation.y = Math.atan2(Math.cos(t * 0.2), -Math.sin(t * 0.2));
    }
  });

  const color = type === 'sheep' ? '#f0f0e8' : '#a0826d';
  return (
    <group ref={ref} position={position}>
      <mesh position={[0, 0.5, 0]} castShadow>
        <boxGeometry args={[0.6, 0.5, 1.2]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[0, 0.7, 0.5]} castShadow>
        <sphereGeometry args={[0.25, 8, 8]} />
        <meshStandardMaterial color={color} />
      </mesh>
    </group>
  );
};

export const MultiLayerFarm3D: React.FC<MultiLayerFarm3DProps> = ({
  showCanopy = true,
  showSubCanopy = true,
  showGround = true,
  showAnimals = true,
}) => {
  const treePositions: [number, number, number][] = [
    [-8, 0, -8], [8, 0, -8], [-8, 0, 8], [8, 0, 8],
    [0, 0, -10], [0, 0, 10], [-10, 0, 0], [10, 0, 0],
  ];

  const bushPositions: [number, number, number][] = [
    [-4, 0, -4], [4, 0, -4], [-4, 0, 4], [4, 0, 4],
    [0, 0, -6], [0, 0, 6], [-6, 0, 0], [6, 0, 0],
  ];

  const groundPositions: [number, number, number][] = [];
  for (let i = -12; i <= 12; i += 2) {
    for (let j = -12; j <= 12; j += 2) {
      groundPositions.push([i + Math.random() * 0.5, 0.25, j + Math.random() * 0.5]);
    }
  }

  return (
    <div style={{ width: '100%', height: 600, borderRadius: 'var(--radius-lg)', overflow: 'hidden', background: 'linear-gradient(to bottom, #87CEEB, #E0F6FF)' }}>
      <Canvas shadows>
        <Sky sunPosition={[100, 50, 100]} />
        <ambientLight intensity={0.6} />
        <directionalLight
          position={[30, 30, 30]}
          intensity={1.2}
          castShadow
          shadow-mapSize={[2048, 2048]}
        />

        {/* زمین */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
          <planeGeometry args={[40, 40]} />
          <meshStandardMaterial color="#8fbc8f" roughness={0.9} />
        </mesh>

        {/* لایه بالایی: درختان */}
        {showCanopy && treePositions.map((pos, i) => (
          <CanopyTree
            key={`tree-${i}`}
            position={pos}
            species={['walnut', 'olive', 'pistachio'][i % 3]}
          />
        ))}

        {/* لایه میانی: بوته‌ها */}
        {showSubCanopy && bushPositions.map((pos, i) => (
          <SubCanopyBush key={`bush-${i}`} position={pos} />
        ))}

        {/* لایه زمینی: گیاهان پوششی */}
        {showGround && groundPositions.map((pos, i) => (
          <GroundCrop
            key={`ground-${i}`}
            position={pos}
            type={['clover', 'alfalfa', 'mint', 'saffron'][i % 4]}
          />
        ))}

        {/* دام‌ها */}
        {showAnimals && Array.from({ length: 8 }).map((_, i) => (
          <GrazingAnimal
            key={`animal-${i}`}
            position={[
              (Math.random() - 0.5) * 20,
              0,
              (Math.random() - 0.5) * 20,
            ]}
            type={i % 2 === 0 ? 'sheep' : 'goat'}
          />
        ))}

        <OrbitControls enablePan enableZoom enableRotate />
      </Canvas>
    </div>
  );
};
