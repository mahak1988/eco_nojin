import { Suspense, useEffect } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, ContactShadows, Preload } from '@react-three/drei';
import * as THREE from 'three';
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

/**
 * Quality enhancer component - applies anisotropic filtering to all textures
 * and optimizes renderer settings for ultra HD output
 */
function QualityEnhancer() {
  const { gl, scene } = useThree();

  useEffect(() => {
    // Enable high-quality texture filtering
    const maxAniso = gl.capabilities.getMaxAnisotropy();
    
    scene.traverse((obj) => {
      if ((obj as THREE.Mesh).isMesh) {
        const mesh = obj as THREE.Mesh;
        const mat = mesh.material as THREE.Material & { map?: THREE.Texture; normalMap?: THREE.Texture };
        
        if (mat.map) {
          mat.map.anisotropy = Math.min(16, maxAniso);
          mat.map.minFilter = THREE.LinearMipmapLinearFilter;
          mat.map.magFilter = THREE.LinearFilter;
          mat.map.generateMipmaps = true;
          mat.map.needsUpdate = true;
        }
        
        if (mat.normalMap) {
          mat.normalMap.anisotropy = Math.min(16, maxAniso);
          mat.normalMap.needsUpdate = true;
        }
      }
    });

    // Renderer optimizations
    gl.outputColorSpace = THREE.SRGBColorSpace;
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.1;
    
    // Enable physically correct lights
    gl.physicallyCorrectLights = true;
    
    console.log(`🎬 UHD Render Quality Active: Anisotropy=${Math.min(16, maxAniso)}x`);
  }, [gl, scene]);

  return null;
}

function Scene() {
  const { condition, timeOfDay } = useWeatherStore();
  const a = useArtisticStore();

  return (
    <>
      <QualityEnhancer />
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
      {a.enableBirds && timeOfDay !== 'night' && condition !== 'storm' && condition !== 'dust' && <Birds />}
      {a.enableButterflies && timeOfDay === 'day' && condition === 'clear' && <Butterflies />}
      {a.enableGodRays && timeOfDay !== 'night' && condition !== 'dust' && condition !== 'storm' && <GodRays />}

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

      {/* Enhanced contact shadows - softer and wider */}
      <ContactShadows 
        position={[0, 0.05, 0]} 
        opacity={0.5} 
        scale={600} 
        blur={2.5} 
        far={80}
        resolution={1024}
        color="#1a2a3a"
      />
      
      <OrbitControls 
        makeDefault 
        enablePan 
        enableZoom 
        enableRotate 
        minDistance={20}
        maxDistance={600}
        maxPolarAngle={Math.PI / 2.05}
        target={[0, 0, 0]}
        enableDamping
        dampingFactor={0.05}
      />
      
      <Preload all />
    </>
  );
}

export function CinematicSimulator() {
  const { timeOfDay, condition } = useWeatherStore();

  // Dynamic exposure based on weather/time
  const exposure = (() => {
    let base = 1.1;
    if (timeOfDay === 'night') base = 0.6;
    else if (timeOfDay === 'dawn' || timeOfDay === 'dusk') base = 0.9;
    if (condition === 'dust') base *= 0.5;
    if (condition === 'storm') base *= 0.4;
    return base;
  })();

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#000' }}>
      <Canvas
        shadows="soft"
        camera={{ 
          position: [150, 80, 150],
          fov: 65,  // Slightly narrower for more cinematic look
          near: 0.1, 
          far: 5000
        }}
        gl={{ 
          antialias: true,
          alpha: false,
          powerPreference: 'high-performance',
          stencil: false,
          depth: true,
          preserveDrawingBuffer: false,
          logarithmicDepthBuffer: true,  // Better z-fighting prevention
        }}
        dpr={[2, 3]}  // Ultra HD: 2x to 3x device pixel ratio
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = exposure;
          gl.outputColorSpace = THREE.SRGBColorSpace;
          // Enable shadow map
          gl.shadowMap.enabled = true;
          gl.shadowMap.type = THREE.PCFSoftShadowMap;
        }}
      >
        <Suspense fallback={null}>
          <Scene />
        </Suspense>
      </Canvas>
      <CinematicOverlay />
      <WeatherControls />
      
      {/* UHD Quality Indicator */}
      <div style={{
        position: 'absolute',
        bottom: 10,
        left: 10,
        color: 'rgba(255,255,255,0.5)',
        fontSize: 11,
        fontFamily: 'monospace',
        pointerEvents: 'none',
        zIndex: 100,
      }}>
        🎬 UHD RENDER ACTIVE | DPR: {window.devicePixelRatio.toFixed(1)}x | PCF Soft Shadows
      </div>
    </div>
  );
}

export default CinematicSimulator;
