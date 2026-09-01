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

  return (
    <>
      <SeasonController />
      <CinematicCamera />
      <LightingSystem />
      <Terrain />
      <VegetationSystem />
      <WeatherEffects />
      {!a.enableFlood && <WaterSystem />}
      <PostProcessing />

      {/* Artistic atmospheric effects */}
      {a.enableAurora && timeOfDay === 'night' && <Aurora />}
      {condition === 'storm' && <Lightning />}
      {a.enableRainbow && (condition === 'rain' || condition === 'clear') && timeOfDay === 'day' && <Rainbow />}
      {a.enableFireflies && timeOfDay === 'night' && <Fireflies />}
      {a.enableBirds && timeOfDay !== 'night' && condition !== 'storm' && <Birds />}
      {a.enableButterflies && timeOfDay === 'day' && condition === 'clear' && <Butterflies />}
      {a.enableGodRays && timeOfDay !== 'night' && condition !== 'dust' && <GodRays />}

      {/* Agricultural elements */}
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

      <ContactShadows position={[0, 0.1, 0]} opacity={0.4} scale={200} blur={2} far={30} />
      <OrbitControls makeDefault enablePan enableZoom enableRotate minDistance={5} maxDistance={200} maxPolarAngle={Math.PI / 2.1} />
    </>
  );
}

export function CinematicSimulator() {
  const { timeOfDay } = useWeatherStore();

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#000' }}>
      <Canvas
        shadows
        camera={{ position: [50, 30, 50], fov: 60, near: 0.1, far: 2000 }}
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
