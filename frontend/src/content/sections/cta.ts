import type { SiteContent } from './types';

export interface CtaContent {
  fa: SiteContent['cta'];
  en: SiteContent['cta'];
}

export const cta = {
  fa: {
    title: 'زمین منتظر نمی‌ماند',
    lead: 'برای پایلوت، همکاری پژوهشی یا سرمایه‌گذاری اثرگذار، با ما در تماس باشید.',
    button: 'شروع گفت‌وگو',
  },
  en: {
    title: 'The land won’t wait',
    lead: 'For pilots, research partnerships or impact investment, get in touch.',
    button: 'Start the conversation',
  },
} as const;

export type CtaLang = 'fa' | 'en';
