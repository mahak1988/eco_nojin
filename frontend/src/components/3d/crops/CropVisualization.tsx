import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface CropVisualizationProps {
  rows?: number;
  cols?: number;
  growthStage?: number; // 0-1
  cropType?: 'wheat' | 'maize' | 'tree';
  ndvi?: number; // 0-1
}

/**
 * شبیه‌سازی رشد گیاه سه‌بعدی
 */
export const CropVisualization: React.FC<CropVisualizationProps> = ({
  rows = 20,
  cols = 20,
  growthStage = 0.5,
  cropType = 'wheat',
  ndvi = 0.7,
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const timeRef = useRef(0);

  useFrame((_state, delta) => {
    timeRef.current += delta;
    // انیمیشن باد
    if (groupRef.current) {
      groupRef.current.children.forEach((child, i) => {
        child.rotation.x = Math.sin(timeRef.current + i * 0.1) * 0.05;
        child.rotation.z = Math.cos(timeRef.current + i * 0.15) * 0.05;
      });
    }
  });

  const plants = useMemo(() => {
    const items = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const x = (c - cols / 2) * 2;
        const z = (r - rows / 2) * 2;
        const variation = 0.8 + Math.random() * 0.4;
        const height = growthStage * variation;

        let color = new THREE.Color();
        if (ndvi < 0.3)
          color.setHex(0x8b7355); // خشک
        else if (ndvi < 0.5)
          color.setHex(0xa0a050); // ضعیف
        else if (ndvi < 0.7)
          color.setHex(0x90c966); // متوسط
        else color.setHex(0x3d8b3d); // سالم

        items.push({ x, z, height, color, key: `${r}-${c}` });
      }
    }
    return items;
  }, [rows, cols, growthStage, ndvi]);

  if (cropType === 'tree') {
    return (
      <group ref={groupRef}>
        {plants.map((p) => (
          <group key={p.key} position={[p.x, 0, p.z]}>
            {/* تنه */}
            <mesh position={[0, p.height * 1.5, 0]} castShadow>
              <cylinderGeometry args={[0.2, 0.3, p.height * 3, 8]} />
              <meshStandardMaterial color="#6b4423" />
            </mesh>
            {/* تاج */}
            <mesh position={[0, p.height * 3, 0]} castShadow>
              <sphereGeometry args={[p.height * 1.5, 16, 16]} />
              <meshStandardMaterial color={p.color} />
            </mesh>
          </group>
        ))}
      </group>
    );
  }

  return (
    <group ref={groupRef}>
      {plants.map((p) => (
        <mesh key={p.key} position={[p.x, p.height, p.z]} castShadow>
          <coneGeometry args={[0.15, p.height * 2, 6]} />
          <meshStandardMaterial color={p.color} />
        </mesh>
      ))}
    </group>
  );
};
