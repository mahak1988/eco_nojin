import type { SiteContent } from './types';

export interface StatsContent {
  fa: SiteContent['stats'];
  en: SiteContent['stats'];
}

export const stats = {
  fa: [
    { value: '+۳۰', label: 'زیرماژول علمی در موتور هیدروما' },
    { value: '۳۸', label: 'سرویس میکروسرویسی' },
    { value: '۵', label: 'کانال دسترسی: وب تا صوت' },
    { value: '۱۴', label: 'زبان برای جوامع محلی' },
    { value: '۲.۵ میلیارد', label: 'کشاورز خرد، مخاطب هدف' },
    { value: '۵', label: 'شاخص پوشش گیاهی؛ NDVI تا NBR' },
  ],
  en: [
    { value: '30+', label: 'scientific submodules in HyDroMa' },
    { value: '38', label: 'microservices' },
    { value: '5', label: 'access channels, web to voice' },
    { value: '14', label: 'languages for local communities' },
    { value: '2.5B', label: 'smallholder farmers in scope' },
    { value: '5', label: 'vegetation indices, NDVI to NBR' },
  ],
} as const;

export type StatsLang = 'fa' | 'en';
