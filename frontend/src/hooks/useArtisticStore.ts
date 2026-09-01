import { create } from 'zustand';

export type Season = 'spring' | 'summer' | 'autumn' | 'winter';

export interface ArtisticState {
  season: Season;
  enableAurora: boolean;
  enableRainbow: boolean;
  enableFireflies: boolean;
  enableBirds: boolean;
  enableButterflies: boolean;
  enableGodRays: boolean;      // deprecated - kept false, no longer rendered
  enableSunCycle: boolean;     // NEW: moving sun day cycle
  enableCinematicCamera: boolean;
  enableLetterbox: boolean;
  enableFilmGrain: boolean;
  enableLensFlare: boolean;
  timeScale: number;
  enableInsects: boolean;
  enableDomesticAnimals: boolean;
  enablePoultry: boolean;
  enableFlood: boolean;
  enableIrrigation: boolean;
  enableWell: boolean;
  enableRiver: boolean;
  enableCoastline: boolean;
  enableWatershed: boolean;
  enablePlowing: boolean;

  setSeason: (s: Season) => void;
  toggle: (key: string) => void;
  setTimeScale: (t: number) => void;
}

export const useArtisticStore = create<ArtisticState>((set) => ({
  season: 'summer',
  enableAurora: false,
  enableRainbow: false,
  enableFireflies: false,
  enableBirds: true,
  enableButterflies: true,
  enableGodRays: false,
  enableSunCycle: true,
  enableCinematicCamera: false,
  enableLetterbox: true,
  enableFilmGrain: true,
  enableLensFlare: false,
  timeScale: 1,
  enableInsects: true,
  enableDomesticAnimals: true,
  enablePoultry: true,
  enableFlood: false,
  enableIrrigation: true,
  enableWell: true,
  enableRiver: true,
  enableCoastline: true,
  enableWatershed: true,
  enablePlowing: true,

  setSeason: (season) => set({ season }),
  toggle: (key) => set((s) => ({ [key]: !(s as any)[key] })),
  setTimeScale: (timeScale) => set({ timeScale }),
}));
