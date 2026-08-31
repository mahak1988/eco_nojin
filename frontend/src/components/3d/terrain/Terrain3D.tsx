import React, { useRef, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Sky, Grid } from '@react-three/drei';
import * as THREE from 'three';

interface TerrainProps {
  width?: number;
  depth?: number;
  segments?: number;
  heightScale?: number;
  colorScheme?: 'natural' | 'elevation' | 'ndvi';
}

/**
 * زمین سه‌بعدی با terrain elevation
 */
const TerrainMesh: React.FC<TerrainProps> = ({
  width = 100,
  depth = 100,
  segments = 50,
  heightScale = 5,
  colorScheme = 'natural',
}) => {
  const meshRef = useRef<THREE.Mesh>(null);

  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(width, depth, segments, segments);
    const positions = geo.attributes.position;

    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      // تپه‌های سینوسی (شبیه‌سازی DEM)
      const z =
        Math.sin(x / 20) * Math.cos(y / 20) * heightScale +
        Math.sin(x / 8) * 1.5 +
        Math.cos(y / 12) * 1.2;
      positions.setZ(i, z);
    }

    geo.computeVertexNormals();

    // رنگ‌آمیزی بر اساس ارتفاع
    const colors = [];
    for (let i = 0; i < positions.count; i++) {
      const z = positions.getZ(i);
      let color = new THREE.Color();
      if (colorScheme === 'elevation') {
        color.setHSL(0.3 - (z / heightScale) * 0.2, 0.7, 0.5);
      } else if (colorScheme === 'ndvi') {
        const ndvi = (z + heightScale) / (2 * heightScale);
        color.setHSL(0.25 + ndvi * 0.1, 0.6, 0.4);
      } else {
        // طبیعی
        if (z < 0)
          color.setHex(0x8b7355); // خاک
        else if (z < 2)
          color.setHex(0x90c966); // علف
        else color.setHex(0x6b8e4e); // بوته
      }
      colors.push(color.r, color.g, color.b);
    }
    geo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

    return geo;
  }, [width, depth, segments, heightScale, colorScheme]);

  return (
    <mesh
      ref={meshRef}
      geometry={geometry}
      rotation={[-Math.PI / 2, 0, 0]}
      receiveShadow
      castShadow
    >
      <meshStandardMaterial vertexColors side={THREE.DoubleSide} roughness={0.8} />
    </mesh>
  );
};

interface Terrain3DSceneProps extends TerrainProps {}

export const Terrain3DScene: React.FC<Terrain3DSceneProps> = (props) => {
  return (
    <div style={{ width: '100%', height: '600px', background: '#87CEEB' }}>
      <Canvas shadows camera={{ position: [60, 40, 60], fov: 50 }}>
        <Sky sunPosition={[100, 50, 100]} />
        <ambientLight intensity={0.4} />
        <directionalLight
          position={[50, 50, 50]}
          intensity={1}
          castShadow
          shadow-mapSize={[2048, 2048]}
        />
        <TerrainMesh {...props} />
        <Grid infiniteGrid cellSize={10} sectionSize={50} fadeDistance={200} />
        <OrbitControls enablePan enableZoom enableRotate />
      </Canvas>
    </div>
  );
};
