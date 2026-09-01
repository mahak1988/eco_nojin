import { CustomWater } from './CustomWater';
import { LAKE_LEVEL } from '../../utils/terrainHeight';
import { useWeatherStore } from '../../hooks/useWeatherStore';

export function WaterSystem() {
  const { condition, timeOfDay } = useWeatherStore();

  const waterColor = (() => {
    if (condition === 'drought') return '#8b7355';
    if (condition === 'dust') return '#a0826b';
    if (timeOfDay === 'dawn') return '#ff9a6b';
    if (timeOfDay === 'dusk') return '#d85a7a';
    if (timeOfDay === 'night') return '#1a2a4a';
    return '#2a5a8a';
  })();

  const waveHeight = condition === 'storm' ? 0.5 : condition === 'rain' ? 0.3 : 0.15;

  return (
    <CustomWater
      position={[0, LAKE_LEVEL, 0]}
      radius={55}
      color={waterColor}
      waveHeight={waveHeight}
      waveSpeed={condition === 'storm' ? 1.2 : 0.5}
    />
  );
}
