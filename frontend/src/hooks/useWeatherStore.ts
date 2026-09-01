import { create } from 'zustand';

export type WeatherCondition = 'clear' | 'rain' | 'snow' | 'dust' | 'drought' | 'storm';
export type TimeOfDay = 'dawn' | 'day' | 'dusk' | 'night';

export interface WeatherState {
  condition: WeatherCondition;
  intensity: number; // 0-1
  windSpeed: number; // 0-100 km/h
  windDirection: number; // 0-360 degrees
  timeOfDay: TimeOfDay;
  sunPosition: [number, number, number];
  temperature: number; // -20 to 50 C
  humidity: number; // 0-100%
  plantGrowthStage: number; // 0-1
  fogDensity: number; // 0-1
  enablePostProcessing: boolean;
  
  setCondition: (c: WeatherCondition) => void;
  setIntensity: (i: number) => void;
  setWind: (speed: number, dir: number) => void;
  setTimeOfDay: (t: TimeOfDay) => void;
  setTemperature: (t: number) => void;
  setPlantGrowth: (g: number) => void;
  setFogDensity: (d: number) => void;
  togglePostProcessing: () => void;
}

const sunPositions: Record<TimeOfDay, [number, number, number]> = {
  dawn: [100, 20, 100],
  day: [100, 100, 50],
  dusk: [-100, 20, 100],
  night: [0, -50, 0],
};

export const useWeatherStore = create<WeatherState>((set) => ({
  condition: 'clear',
  intensity: 0.7,
  windSpeed: 15,
  windDirection: 45,
  timeOfDay: 'day',
  sunPosition: sunPositions.day,
  temperature: 25,
  humidity: 50,
  plantGrowthStage: 0.5,
  fogDensity: 0.2,
  enablePostProcessing: true,
  
  setCondition: (condition) => set({ condition }),
  setIntensity: (intensity) => set({ intensity: Math.max(0, Math.min(1, intensity)) }),
  setWind: (speed, direction) => set({ windSpeed: speed, windDirection: direction }),
  setTimeOfDay: (timeOfDay) => set({ timeOfDay, sunPosition: sunPositions[timeOfDay] }),
  setTemperature: (temperature) => set({ temperature }),
  setPlantGrowth: (growth) => set({ plantGrowthStage: Math.max(0, Math.min(1, growth)) }),
  setFogDensity: (density) => set({ fogDensity: density }),
  togglePostProcessing: () => set((s) => ({ enablePostProcessing: !s.enablePostProcessing })),
}));
