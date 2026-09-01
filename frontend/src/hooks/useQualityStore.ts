import { create } from 'zustand';

export type QualityTier = 'high' | 'medium' | 'low';

interface QualityState {
  tier: QualityTier;
  setTier: (t: QualityTier) => void;
}

/**
 * Adaptive quality tier.
 * NOTE: zustand (not React Context) because React context does NOT
 * cross the R3F Canvas boundary.
 */
export const useQualityStore = create<QualityState>((set) => ({
  tier: 'high',
  setTier: (tier) => set({ tier }),
}));

export const TIER_LABEL: Record<QualityTier, string> = {
  high: 'بالا',
  medium: 'متوسط',
  low: 'پایین',
};
