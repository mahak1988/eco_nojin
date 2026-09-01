import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows } from '@react-three/drei';
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
import { GodRays } from './GodRays';
import { CinematicCamera } from './CinematicCamera';
import { CinematicOverlay } from './CinematicOverlay';
import { SeasonController } from './SeasonController';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';

function Scene() {
  const { condition, timeOfDay } = useWeatherStore();
  const {
    enableAurora, enableRainbow, enableFireflies, enableBirds,
    enableButterflies, enableGodRays,
  } = useArtisticStore();

  return (
    <>
      <SeasonController />
      <CinematicCamera />
      <LightingSystem />
      <Terrain />
      <VegetationSystem />
      <WeatherEffects />
      <WaterSystem />
      <PostProcessing />

      {/* Artistic effects */}
      {enableAurora && timeOfDay === 'night' && <Aurora />}
      {condition === 'storm' && <Lightning />}
      {enableRainbow && (condition === 'rain' || condition === 'clear') && timeOfDay === 'day' && <Rainbow />}
      {enableFireflies && timeOfDay === 'night' && <Fireflies />}
      {enableBirds && timeOfDay !== 'night' && condition !== 'storm' && <Birds />}
      {enableButterflies && timeOfDay === 'day' && condition === 'clear' && <Butterflies />}
      {enableGodRays && timeOfDay !== 'night' && condition !== 'dust' && <GodRays />}

      <ContactShadows position={[0, 0.1, 0]} opacity={0.4} scale={100} blur={2} far={20} />
      <OrbitControls makeDefault enablePan enableZoom enableRotate minDistance={5} maxDistance={150} maxPolarAngle={Math.PI / 2.1} />
    </>
  );
}

export function CinematicSimulator() {
  const { timeOfDay } = useWeatherStore();

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#000' }}>
      <Canvas
        shadows
        camera={{ position: [30, 20, 30], fov: 60, near: 0.1, far: 1000 }}
        gl={{ antialias: true, toneMapping: 4, toneMappingExposure: timeOfDay === 'night' ? 0.5 : 1.0 }}
        dpr={[1, 2]}
      >
        <Suspense fallback={null}>
          <Scene />
        </Suspense>
      </Canvas>
      <CinematicOverlay />
      <WeatherControls />
    </div>
  );
}

export default CinematicSimulator;
