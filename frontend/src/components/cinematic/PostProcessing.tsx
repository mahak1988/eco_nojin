import { EffectComposer, Bloom, DepthOfField, Vignette, ChromaticAberration, HueSaturation, BrightnessContrast } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import { N8AO } from '@react-three/postprocessing';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';
import { Vector2 } from 'three';

export function PostProcessing() {
  const { enablePostProcessing, condition, timeOfDay } = useArtisticStore();
  const weather = useWeatherStore();

  if (!enablePostProcessing) return null;

  // Color grading based on weather
  const hueShift = (() => {
    if (weather.condition === 'drought') return -0.05;
    if (weather.condition === 'snow') return 0.05;
    if (weather.condition === 'dust') return -0.08;
    return 0;
  })();

  const saturation = (() => {
    if (weather.condition === 'drought') return -0.25;
    if (weather.condition === 'dust') return -0.4;
    if (weather.condition === 'storm') return -0.3;
    if (weather.timeOfDay === 'night') return -0.4;
    if (weather.timeOfDay === 'dawn' || weather.timeOfDay === 'dusk') return 0.15;
    return 0.08;
  })();

  const brightness = (() => {
    if (weather.condition === 'storm' || weather.condition === 'dust') return -0.15;
    if (weather.timeOfDay === 'night') return -0.2;
    return 0;
  })();

  const contrast = (() => {
    if (weather.timeOfDay === 'dawn' || weather.timeOfDay === 'dusk') return 0.15;
    if (weather.condition === 'dust') return -0.1;
    return 0.05;
  })();

  return (
    <EffectComposer 
      multisampling={8}  // 8x MSAA for ultra-smooth edges
      frameBufferType={THREE.HalfFloatType}  // HDR rendering
    >
      {/* Ultra quality SSAO via N8AO */}
      <N8AO
        aoRadius={0.8}
        intensity={2.5}
        distanceFalloff={0.8}
        color="#1a1a2e"
        quality="ultra"  // Ultra quality preset
        halfRes={false}  // Full resolution
      />

      {/* Enhanced Bloom with mipmapped blur */}
      <Bloom
        intensity={weather.timeOfDay === 'night' ? 1.2 : 0.5}
        luminanceThreshold={0.75}
        luminanceSmoothing={0.85}
        mipmapBlur
        radius={0.85}
        levels={8}
      />

      {/* Cinematic Depth of Field */}
      <DepthOfField
        focusDistance={0.015}
        focalLength={0.04}
        bokehScale={2.5}
        height={720}
      />

      {/* Brightness & Contrast for cinematic look */}
      <BrightnessContrast
        brightness={brightness}
        contrast={contrast}
      />

      {/* Color grading */}
      <HueSaturation
        hue={hueShift}
        saturation={saturation}
      />

      {/* Cinematic Vignette */}
      <Vignette
        eskil={false}
        offset={0.25}
        darkness={0.85}
      />

      {/* Chromatic aberration for storm/dust */}
      {(weather.condition === 'storm' || weather.condition === 'dust') && (
        <ChromaticAberration
          offset={new Vector2(0.0015, 0.0015)}
          radialModulation={true}
          modulationOffset={0.5}
        />
      )}
    </EffectComposer>
  );
}
