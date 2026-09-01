import { create } from 'zustand';

export type Season = 'spring' | 'summer' | 'autumn' | 'winter';

export interface ArtisticState {
  season: Season;
  enableAurora: boolean;
  enableRainbow: boolean;
  enableFireflies: boolean;
  enableBirds: boolean;
  enableButterflies: boolean;
  enableGodRays: boolean;
  enableCinematicCamera: boolean;
  enableLetterbox: boolean;
  enableFilmGrain: boolean;
  enableLensFlare: boolean;
  timeScale: number;

  setSeason: (s: Season) => void;
  toggle: (key: keyof Omit<ArtisticState, 'season' | 'timeScale' | 'setSeason' | 'toggle' | 'setTimeScale'>) => void;
  setTimeScale: (t: number) => void;
}

export const useArtisticStore = create<ArtisticState>((set) => ({
  season: 'summer',
  enableAurora: false,
  enableRainbow: false,
  enableFireflies: false,
  enableBirds: true,
  enableButterflies: true,
  enableGodRays: true,
  enableCinematicCamera: false,
  enableLetterbox: true,
  enableFilmGrain: true,
  enableLensFlare: false,
  timeScale: 1,

  setSeason: (season) => set({ season }),
  toggle: (key) => set((s) => ({ [key]: !s[key] } as any)),
  setTimeScale: (timeScale) => set({ timeScale }),
}));
