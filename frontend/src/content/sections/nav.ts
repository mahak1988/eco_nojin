import type { SiteContent } from './types';

export interface NavContent {
  fa: SiteContent['nav'];
  en: SiteContent['nav'];
}

export const nav = {
  fa: {
    home: 'خانه',
    platform: 'پلتفرم',
    science: 'علم هیدروما',
    about: 'درباره و تماس',
    blog: 'بلاگ',
    langLabel: 'EN',
  },
  en: {
    home: 'Home',
    platform: 'Platform',
    science: 'HyDroMa Science',
    about: 'About & Contact',
    blog: 'Blog',
    langLabel: 'فا',
  },
} as const;

export type NavLang = 'fa' | 'en';
