import type { SiteContent } from './types';

export interface BrandContent {
  fa: SiteContent['brand'];
  en: SiteContent['brand'];
}

export const brand = {
  fa: {
    name: 'اکو نوژین',
    latin: 'Eco Nojin',
    tagline: 'احیای زمین با دقتِ ماهواره‌ای',
  },
  en: {
    name: 'Eco Nojin',
    latin: 'Eco Nojin',
    tagline: 'Restoring land with satellite-grade precision',
  },
} as const;

export type BrandLang = 'fa' | 'en';
