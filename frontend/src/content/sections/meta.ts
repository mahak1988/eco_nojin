import type { SiteContent } from './types';

export interface MetaContent {
  fa: SiteContent['meta'];
  en: SiteContent['meta'];
}

export const meta = {
  fa: {
    title: 'اکو نوژین | احیای اکوسیستم با دقت ماهواره‌ای',
    description:
      'اکو نوژین — پلتفرم علمی احیای اکوسیستم، کشاورزی هوشمند و اقتصاد کربن؛ با موتور علمی هیدروما و پایش ماهواره‌ای سنتینل.',
  },
  en: {
    title: 'Eco Nojin | Ecosystem restoration with satellite-grade precision',
    description:
      'Eco Nojin — a scientific platform for ecosystem restoration, smart agriculture and the carbon economy, powered by the HyDroMa engine and Sentinel monitoring.',
  },
} as const;

export type MetaLang = 'fa' | 'en';
