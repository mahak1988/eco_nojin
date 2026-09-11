import type { SiteContent } from './types';

export interface CommonContent {
  fa: SiteContent['common'];
  en: SiteContent['common'];
}

export const common = {
  fa: {
    conceptual: 'تصویرسازی مفهومی',
    learnMore: 'بیشتر بدانید',
  },
  en: {
    conceptual: 'Conceptual illustration',
    learnMore: 'Learn more',
  },
} as const;

export type CommonLang = 'fa' | 'en';
