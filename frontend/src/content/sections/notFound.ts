import type { SiteContent } from './types';

export interface NotfoundContent {
  fa: SiteContent['notFound'];
  en: SiteContent['notFound'];
}

export const notFound = {
  fa: {
    title: '۴۰۴ — صفحه پیدا نشد',
    lead: 'نشانی‌ای که دنبالش بودید وجود ندارد یا جابه‌جا شده است.',
    homeButton: 'بازگشت به خانه',
  },
  en: {
    title: '404 — Page not found',
    lead: 'The address you were looking for doesn’t exist or has moved.',
    homeButton: 'Back to home',
  },
} as const;

export type NotfoundLang = 'fa' | 'en';
