import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Sky, Grid, Environment } from '@react-three/drei';
import { Terrain3DScene } from './terrain/Terrain3D';
import { CropVisualization } from './crops/CropVisualization';
import { AnimalHerd } from './animals/AnimalAnimation';

interface FarmScene3DProps {
  showTerrain?: boolean;
  showCrops?: boolean;
  cropType?: 'wheat' | 'maize' | 'tree';
  growthStage?: number;
  ndvi?: number;
  herds?: Array<{ type: 'cattle' | 'sheep' | 'goat' | 'poultry'; count: number }>;
}

/**
 * صحنه سه‌بعدی کامل مزرعه
 */
export const FarmScene3D: React.FC<FarmScene3DProps> = ({
  showTerrain = true,
  showCrops = true,
  cropType = 'wheat',
  growthStage = 0.6,
  ndvi = 0.7,
  herds = [] }) => {
  return (
    <div style={{ width: '100%', height: '700px', background: 'linear-gradient(to bottom, #87CEEB, #E0F6FF)' }}>
      <Canvas shadows camera={{ position: [50, 40, 50], fov: 50 }}>
        <Sky sunPosition={[100, 50, 100]} />
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[50, 50, 50]}
          intensity={1.2}
          castShadow
          shadow-mapSize={[2048, 2048]}
        />

        {showTerrain && <Terrain3DScene />}

        {showCrops && (
          <group position={[0, 0.1, 0]}>
            <CropVisualization
              cropType={cropType}
              growthStage={growthStage}
              ndvi={ndvi}
              rows={15}
              cols={15}
            />
          </group>
        )}

        {herds.map((herd, i) => (
          <AnimalHerd key={i} herd={herd} />
        ))}

        <Grid
          infiniteGrid
          cellSize={5}
          sectionSize={50}
          fadeDistance={300}
          cellColor="#666"
          sectionColor="#333"
        />

        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          minDistance={20}
          maxDistance={200}
        />
      </Canvas>
    </div>
  );
};
