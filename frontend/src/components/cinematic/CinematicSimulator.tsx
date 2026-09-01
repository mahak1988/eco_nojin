import { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Preload } from '@react-three/drei';
import * as THREE from 'three';
import { useQualityStore, TIER_LABEL } from '../../hooks/useQualityStore';
import { PerformanceGovernor } from './PerformanceGovernor';
import { CameraIntro } from './CameraIntro';
import { Terrain } from './Terrain';
import { WeatherEffects } from './WeatherEffects';
import { VegetationSystem } from './VegetationSystem';
import { LightingSystem } from './LightingSystem';
import { PostProcessing } from './PostProcessing';
import { WaterSystem } from './WaterSystem';
import { WeatherControls } from './WeatherControls';
import { Aurora } from './Aurora';
import { Lightning } from './Lightning';
import { Rainbow } from './Rainbow';
import { Fireflies } from './Fireflies';
import { Birds } from './Birds';
import { Butterflies } from './Butterflies';
import { CinematicCamera } from './CinematicCamera';
import { CinematicOverlay } from './CinematicOverlay';
import { SeasonController } from './SeasonController';
import { InsectsSystem } from './InsectsSystem';
import { DomesticAnimals } from './DomesticAnimals';
import { Poultry } from './Poultry';
import { FloodSimulation } from './FloodSimulation';
import { IrrigationSystem } from './IrrigationSystem';
import { WellSystem } from './WellSystem';
import { RiverSystem } from './RiverSystem';
import { Coastline } from './Coastline';
import { WatershedEngineering } from './WatershedEngineering';
import { PlowingTrails } from './PlowingTrails';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';

function Scene() {
  const { condition, timeOfDay } = useWeatherStore();
  const a = useArtisticStore();
  const [introDone, setIntroDone] = useState(false);

  return (
    <>
      <CameraIntro onDone={() => setIntroDone(true)} />
      <PerformanceGovernor />
      <SeasonController />
      <CinematicCamera />
      <LightingSystem />
      <Terrain />
      <VegetationSystem />
      <WeatherEffects />
      {!a.enableFlood && <WaterSystem />}
      <PostProcessing />

      {a.enableAurora && timeOfDay === 'night' && <Aurora />}
      {condition === 'storm' && <Lightning />}
      {a.enableRainbow && (condition === 'rain' || condition === 'clear') && timeOfDay === 'day' && <Rainbow />}
      {a.enableFireflies && timeOfDay === 'night' && <Fireflies />}
      {a.enableBirds && timeOfDay !== 'night' && condition !== 'storm' && condition !== 'dust' && <Birds />}
      {a.enableButterflies && timeOfDay === 'day' && condition === 'clear' && <Butterflies />}

      {/* NOTE: GodRays removed per user request - replaced by
          moving sun + drifting clouds + real sunshine in LightingSystem */}

      {a.enableInsects && <InsectsSystem />}
      {a.enableDomesticAnimals && <DomesticAnimals />}
      {a.enablePoultry && <Poultry />}
      {a.enableFlood && <FloodSimulation />}
      {a.enableIrrigation && <IrrigationSystem />}
      {a.enableWell && <WellSystem />}
      {a.enableRiver && <RiverSystem />}
      {a.enableCoastline && <Coastline />}
      {a.enableWatershed && <WatershedEngineering />}
      {a.enablePlowing && <PlowingTrails />}

      <OrbitControls
        makeDefault
        enabled={introDone}
        enablePan
        enableZoom
        enableRotate
        minDistance={20}
        maxDistance={600}
        maxPolarAngle={Math.PI / 2.08}
        target={[0, 2, 0]}
        enableDamping
        dampingFactor={0.05}
      />
      <Preload all />
    </>
  );
}

function CanvasHost() {
  const tier = useQualityStore((s) => s.tier);
  const { timeOfDay, condition } = useWeatherStore();

  const dpr: [number, number] =
    tier === 'high' ? [1.25, 1.75] : tier === 'medium' ? [1, 1.25] : [0.75, 1];

  const exposure = (() => {
    let base = 1.1;
    if (timeOfDay === 'night') base = 0.6;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 0.95;
    if (condition === 'dust') base *= 0.55;
    if (condition === 'storm') base *= 0.45;
    return base;
  })();

  return (
    <Canvas
      shadows={tier !== 'low'}
      camera={{ position: [430, 260, 430], fov: 60, near: 0.5, far: 8000 }}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      dpr={dpr}
      onCreated={({ gl }) => {
        gl.toneMapping = THREE.ACESFilmicToneMapping;
        gl.toneMappingExposure = exposure;
        gl.outputColorSpace = THREE.SRGBColorSpace;
        gl.shadowMap.enabled = tier !== 'low';
        gl.shadowMap.type = THREE.PCFSoftShadowMap;
      }}
    >
      <Suspense fallback={null}>
        <Scene />
      </Suspense>
    </Canvas>
  );
}

export function CinematicSimulator() {
  const tier = useQualityStore((s) => s.tier);

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#000' }}>
      <CanvasHost />
      <CinematicOverlay />
      <WeatherControls />
      <div style={{
        position: 'absolute', bottom: 10, left: 10,
        color: 'rgba(255,255,255,0.55)', fontSize: 11, fontFamily: 'monospace',
        pointerEvents: 'none', zIndex: 100, direction: 'rtl',
      }}>
        🎬 کیفیت خودکار: {TIER_LABEL[tier]} | خورشید متحرک + ابرهای متحرک
      </div>
    </div>
  );
}

export default CinematicSimulator;
