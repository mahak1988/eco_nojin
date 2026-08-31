/**
 * SceneContent
 * =============
 * All 3D content rendered inside Canvas + Suspense.
 *
 * This is the heart of the 3D scene containing:
 * - Lighting (ambient + directional)
 * - Sky + Fog + Grid
 * - Terrain meshes (surface + layers)
 * - Decor (forest, crops, barn, silo)
 * - Data plots
 * - Wind arrows
 * - Placed operations
 * - Polygons
 * - Water surface
 * - Rain particles
 * - Camera tour + controller
 * - OrbitControls
 * - Post-processing (Bloom + Vignette)
 *
 * @module features/hydroma/components/viewport/SceneContent
 */

import { Canvas } from '@react-three/fiber';
import { OrbitControls, Sky, Grid } from '@react-three/drei';
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';
import * as THREE from 'three';
import { Suspense } from 'react';

import {
  TerrainMesh,
  PlacedOpsMarkers,
  PolygonOverlay,
  WindArrows,
  WaterSurface,
  RainParticles,
  CameraTour,
  CameraController,
} from '../canvas';

import { useHydromaStore } from '../../store';
import { useEsriTexture } from '../../hooks';
import { useTerrainClick } from '../../hooks';
import {
  DataPlotView,
  Crops,
  Forest,
  Barn,
  Silo,
} from '../../../../components/farmsim/SceneExtras';
import { useTranslation } from 'react-i18next';

export function SceneContent() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  // Store state
  const terrain = useHydromaStore((s) => s.terrain);
  const viewMode = useHydromaStore((s) => s.viewMode);
  const layers = useHydromaStore((s) => s.layers);
  const showNdvi = useHydromaStore((s) => s.showNdvi);
  const visual = useHydromaStore((s) => s.visual);
  const plots = useHydromaStore((s) => s.plots);
  const climate = useHydromaStore((s) => s.climate);
  const placedOps = useHydromaStore((s) => s.placedOps);
  const selectedOp = useHydromaStore((s) => s.selectedOp);
  const polygons = useHydromaStore((s) => s.polygons);
  const currentDrawing = useHydromaStore((s) => s.currentDrawing);
  const tourOn = useHydromaStore((s) => s.tourOn);

  const siteMeta = useHydromaStore((s) => s.siteMeta);
  const setErosionEffect = useHydromaStore((s) => s.setErosionEffect);
  const setTerrain = useHydromaStore((s) => s.setTerrain);
  const setSelectedOp = useHydromaStore((s) => s.setSelectedOp);

  // Hooks
  const esriTexture = useEsriTexture(siteMeta);
  const { handleTerrainClick } = useTerrainClick({
    terrain,
    siteMeta,
    isFa,
    onErosionEffect: setErosionEffect,
    onTerrainUpdate: (updater) => {
      const current = useHydromaStore.getState().terrain;
      setTerrain(updater(current));
    },
  });

  if (!terrain) return null;

  return (
    <Canvas
      shadows
      camera={{ position: [25, 22, 25], fov: 50, near: 0.1, far: 5000 }}
      style={{
        background: 'linear-gradient(180deg, #1e293b 0%, #0f172a 100%)',
      }}
    >
      <Suspense fallback={null}>
        {/* Lighting */}
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[220, 320, 220]}
          intensity={1.2}
          castShadow
          shadow-mapSize={[2048, 2048]}
        />

        {/* Atmosphere */}
        <fog attach="fog" args={['#dfe8d8', 50, 400]} />
        <Sky distance={45000} sunPosition={[100, 30, 100]} />

        {/* Grid */}
        <Grid
          position={[0, -0.5, 0]}
          args={[300, 300]}
          cellSize={10}
          cellColor="#4b5563"
          sectionColor="#374151"
          fadeDistance={200}
        />

        {/* Main terrain (surface + click) */}
        <TerrainMesh
          data={terrain}
          onTerrainClick={handleTerrainClick}
          layer="surface"
          map={esriTexture}
        />

        {/* Optional layers */}
        {layers.soil && <TerrainMesh data={terrain} layer="soil" opacity={0.7} />}
        {layers.bedrock && <TerrainMesh data={terrain} layer="bedrock" opacity={0.6} />}
        {layers.moisture && <TerrainMesh data={terrain} layer="moisture" opacity={0.5} />}
        {layers.roots && <TerrainMesh data={terrain} layer="roots" opacity={0.6} />}
        {layers.groundwater && <TerrainMesh data={terrain} layer="groundwater" opacity={0.5} />}
        {showNdvi && <TerrainMesh data={terrain} layer="ndvi" opacity={0.65} />}

        {/* Decor */}
        {visual.showDecor && (
          <>
            <Forest terrain={terrain as any} />
            <Crops
              terrain={terrain as any}
              center={[-6, 2]}
              size={[10, 8]}
              growth={visual.growth}
              color={
                visual.cropVisual === 'corn'
                  ? '#3f9b3f'
                  : visual.cropVisual === 'wheat'
                    ? '#c9a227'
                    : '#4f8f3f'
              }
            />
            <Barn terrain={terrain as any} position={[4, 0, -12]} rotation={0.3} scale={1.2} />
            <Silo terrain={terrain as any} position={[7, 0, -12]} />
          </>
        )}

        {/* Data plots */}
        {plots.map((p) => (
          <DataPlotView key={p.id} plot={p as any} />
        ))}

        {/* Wind arrows */}
        <WindArrows data={terrain} direction={climate.windDirection} speed={climate.windSpeed} />

        {/* Placed operations */}
        <PlacedOpsMarkers
          ops={placedOps}
          data={terrain}
          selectedId={selectedOp}
          onSelect={setSelectedOp}
        />

        {/* Polygons */}
        <PolygonOverlay polygons={polygons} data={terrain} currentDrawing={currentDrawing} />

        {/* Camera controller */}
        <CameraController viewMode={viewMode} />

        {/* OrbitControls */}
        <OrbitControls
          makeDefault
          enableDamping
          dampingFactor={0.08}
          enableRotate={viewMode === '3d'}
          enableZoom={true}
          enablePan={true}
          minDistance={5}
          maxDistance={150}
          enabled={!tourOn}
          maxPolarAngle={Math.PI / 2 - 0.05}
          zoomSpeed={0.8}
          rotateSpeed={0.8}
          panSpeed={0.8}
          mouseButtons={{
            LEFT: THREE.MOUSE.ROTATE,
            MIDDLE: THREE.MOUSE.DOLLY,
            RIGHT: THREE.MOUSE.PAN,
          }}
          touches={{
            ONE: THREE.TOUCH.ROTATE,
            TWO: THREE.TOUCH.DOLLY_PAN,
          }}
          target={[0, 0, 0]}
        />
      </Suspense>

      {/* Water surface */}
      <WaterSurface levelNorm={0.015} />

      {/* Rain particles */}
      {climate.rainOn && <RainParticles count={1400} />}

      {/* Camera tour */}
      <CameraTour active={tourOn} />

      {/* Post-processing */}
      <EffectComposer multisampling={0}>
        <Bloom intensity={0.38} luminanceThreshold={0.74} mipmapBlur />
        <Vignette offset={0.22} darkness={0.72} />
      </EffectComposer>
    </Canvas>
  );
}
