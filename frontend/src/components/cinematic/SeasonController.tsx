import { useEffect } from 'react';
import { useArtisticStore } from '../../hooks/useArtisticStore';
import { useWeatherStore } from '../../hooks/useWeatherStore';

// Season-based ambient adjustments
export function SeasonController() {
  const { season } = useArtisticStore();
  const setTimeOfDay = useWeatherStore((s) => s.setTimeOfDay);
  const setTemperature = useWeatherStore((s) => s.setTemperature);

  useEffect(() => {
    switch (season) {
      case 'spring':
        setTimeOfDay('day');
        setTemperature(18);
        break;
      case 'summer':
        setTimeOfDay('day');
        setTemperature(35);
        break;
      case 'autumn':
        setTimeOfDay('dusk');
        setTemperature(15);
        break;
      case 'winter':
        setTimeOfDay('day');
        setTemperature(-5);
        break;
    }
  }, [season, setTimeOfDay, setTemperature]);

  return null;
}
