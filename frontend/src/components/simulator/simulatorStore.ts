import { create } from 'zustand';

export type Weather = 'clear' | 'rain' | 'snow' | 'dust' | 'storm';
export type TimeOfDay = 'dawn' | 'day' | 'dusk' | 'night';

interface SimulatorState {
  weather: Weather;
  timeOfDay: TimeOfDay;
  windSpeed: number;
  autoSunCycle: boolean;
  quality: 'low' | 'medium' | 'high';
  
  setWeather: (w: Weather) => void;
  setTimeOfDay: (t: TimeOfDay) => void;
  setWindSpeed: (s: number) => void;
  toggleSunCycle: () => void;
  setQuality: (q: 'low' | 'medium' | 'high') => void;
}

export const useSimulatorStore = create<SimulatorState>((set) => ({
  weather: 'clear',
  timeOfDay: 'day',
  windSpeed: 10,
  autoSunCycle: true,
  quality: 'medium',
  
  setWeather: (weather) => set({ weather }),
  setTimeOfDay: (timeOfDay) => set({ timeOfDay }),
  setWindSpeed: (windSpeed) => set({ windSpeed }),
  toggleSunCycle: () => set((s) => ({ autoSunCycle: !s.autoSunCycle })),
  setQuality: (quality) => set({ quality }),
}));
