import type { SiteContent } from './types';

export interface CarbonContent {
  fa: SiteContent['carbon'];
  en: SiteContent['carbon'];
}

export const carbon = {
  fa: {
    kicker: 'اقتصاد کربن',
    title: 'کربنی که قابل اثبات است',
    lead: 'احیای اکوسیستم باید برای جامعهٔ محلی درآمد بسازد؛ MRV اکو نوژین این مسیر را شفاف می‌کند.',
    bullets: [
      'پایش ماهواره‌ای و میدانی (KoBo) برای اندازه‌گیری واقعی.',
      'ثبت اعتبار کربن با ثبت شبیه‌سازی‌شده روی رجیستری (Polygon testnet/mock).',
      'گزارش MRV شفاف برای خریداران و نهادهای توسعه.',
    ],
    cta: 'مسیر اعتبار کربن',
  },
  en: {
    kicker: 'Carbon economy',
    title: 'Carbon you can prove',
    lead: 'Restoration must pay local communities; Eco Nojin MRV makes that path transparent.',
    bullets: [
      'Satellite and field monitoring (KoBo) for real measurement.',
      'Carbon credits registered with simulated registration on Polygon testnet/mock.',
      'Transparent MRV reporting for buyers and development institutions.',
    ],
    cta: 'The carbon-credit path',
  },
} as const;

export type CarbonLang = 'fa' | 'en';
