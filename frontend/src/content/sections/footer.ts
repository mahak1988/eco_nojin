import type { SiteContent } from './types';

export interface FooterContent {
  fa: SiteContent['footer'];
  en: SiteContent['footer'];
}

export const footer = {
  fa: {
    desc: 'پلتفرم علمی احیای اکوسیستم، کشاورزی هوشمند و اقتصاد کربن — از ماهواره تا مزرعه.',
    exploreTitle: 'کاوش',
    contactTitle: 'تماس',
    legalTitle: 'حقوقی',
    legalLinks: {
      terms: 'شرایط استفاده',
      rules: 'قوانین و مقررات',
      privacy: 'حریم خصوصی',
    },
    quickLinks: {
      faq: 'پرسش‌های متداول',
      contact: 'تماس',
      transparency: 'شفافیت',
    },
    legal: '© ۱۴۰۵ اکو نوژین — منتشرشده با مجوز MIT',
  },
  en: {
    desc: 'The scientific platform for ecosystem restoration, smart agriculture and the carbon economy — from satellite to farm.',
    exploreTitle: 'Explore',
    contactTitle: 'Contact',
    legalTitle: 'Legal',
    legalLinks: {
      terms: 'Terms of Use',
      rules: 'Rules & Regulations',
      privacy: 'Privacy Policy',
    },
    quickLinks: {
      faq: 'FAQ',
      contact: 'Contact',
      transparency: 'Transparency',
    },
    legal: '© 2026 Eco Nojin — released under the MIT License',
  },
} as const;

export type FooterLang = 'fa' | 'en';
