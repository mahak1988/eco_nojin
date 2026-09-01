import { EffectComposer, Bloom, DepthOfField, Vignette, ChromaticAberration, HueSaturation, BrightnessContrast } from '@react-three/postprocessing';
import { N8AO } from '@react-three/postprocessing';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';
import { useQualityStore } from '../../hooks/useQualityStore';
import { Vector2 } from 'three';

export function PostProcessing() {
  const artistic = useArtisticStore();
  const weather = useWeatherStore();
  const tier = useQualityStore((s) => s.tier);

  // Low tier: skip post-processing entirely for max fluidity
  if (!artistic.enablePostProcessing || tier === 'low') return null;

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

  const brightness = (weather.condition === 'storm' || weather.condition === 'dust') ? -0.15 : weather.timeOfDay === 'night' ? -0.2 : 0;
  const contrast = (weather.timeOfDay === 'dawn' || weather.timeOfDay === 'dusk') ? 0.15 : weather.condition === 'dust' ? -0.1 : 0.05;

  return (
    <EffectComposer multisampling={tier === 'high' ? 4 : 0}>
      {tier === 'high' && (
        <N8AO aoRadius={0.8} intensity={2.5} distanceFalloff={0.8} color="#1a1a2e" quality="performance" halfRes />
      )}

      <Bloom
        intensity={weather.timeOfDay === 'night' ? 1.2 : 0.5}
        luminanceThreshold={0.75}
        luminanceSmoothing={0.85}
        mipmapBlur
        radius={0.85}
      />

      {tier === 'high' && (
        <DepthOfField focusDistance={0.015} focalLength={0.04} bokehScale={2.5} height={480} />
      )}

      <BrightnessContrast brightness={brightness} contrast={contrast} />
      <HueSaturation hue={hueShift} saturation={saturation} />
      <Vignette eskil={false} offset={0.25} darkness={0.85} />

      {(weather.condition === 'storm' || weather.condition === 'dust') && (
        <ChromaticAberration offset={new Vector2(0.0015, 0.0015)} radialModulation modulationOffset={0.5} />
      )}
    </EffectComposer>
  );
}
