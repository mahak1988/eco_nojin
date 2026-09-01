import { EffectComposer, Bloom, DepthOfField, Vignette, ChromaticAberration, HueSaturation } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import { N8AO } from '@react-three/postprocessing';
import { useWeatherStore } from '../../hooks/useWeatherStore';
import { Vector2 } from 'three';

export function PostProcessing() {
  const { enablePostProcessing, condition, timeOfDay } = useWeatherStore();

  if (!enablePostProcessing) return null;

  // Color grading based on weather
  const hueShift = (() => {
    if (condition === 'drought') return -0.05;
    if (condition === 'snow') return 0.05;
    return 0;
  })();

  const saturation = (() => {
    if (condition === 'drought') return -0.3;
    if (timeOfDay === 'night') return -0.5;
    if (timeOfDay === 'dawn' || timeOfDay === 'dusk') return 0.2;
    return 0.1;
  })();

  return (
    <EffectComposer multisampling={0}>
      {/* SSAO for ambient occlusion shadows */}
      <N8AO
        aoRadius={1}
        intensity={2}
        distanceFalloff={1}
        color="#000000"
      />

      {/* Bloom for bright light glow */}
      <Bloom
        intensity={timeOfDay === 'night' ? 0.8 : 0.4}
        luminanceThreshold={0.8}
        luminanceSmoothing={0.9}
        mipmapBlur
      />

      {/* Depth of field for cinematic focus */}
      <DepthOfField
        focusDistance={0.01}
        focalLength={0.05}
        bokehScale={3}
        height={480}
      />

      {/* Color grading */}
      <HueSaturation
        hue={hueShift}
        saturation={saturation}
      />

      {/* Vignette for cinematic frame */}
      <Vignette
        eskil={false}
        offset={0.2}
        darkness={0.8}
      />

      {/* Chromatic aberration for storm effect */}
      {(condition === 'storm' || condition === 'dust') && (
        <ChromaticAberration
          offset={new Vector2(0.002, 0.002)}
          radialModulation={true}
          modulationOffset={0.5}
        />
      )}
    </EffectComposer>
  );
}
