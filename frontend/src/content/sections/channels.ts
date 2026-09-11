import type { SiteContent } from './types';

export interface ChannelsContent {
  fa: SiteContent['channels'];
  en: SiteContent['channels'];
}

export const channels = {
  fa: {
    kicker: 'دسترسی برای همه',
    title: 'پنج کانال، یک علم',
    lead: 'هر کس با هر گوشی و هر میزان سواد، به نتیجهٔ علمی می‌رسد.',
    items: [
      { icon: 'globe', title: 'وب و PWA', desc: 'داشبورد کامل با پشتیبانی آفلاین.' },
      { icon: 'sms', title: 'USSD', desc: 'دسترسی از ساده‌ترین گوشی‌ها، بدون اینترنت.' },
      { icon: 'message', title: 'SMS', desc: 'استعلام و اطلاع‌رسانی متنی.' },
      {
        icon: 'bot',
        title: 'ربات پیام‌رسان',
        desc: 'تلگرام، ایتا، بله و روبیکا — همراه همیشگی.',
      },
      { icon: 'mic', title: 'دستیار صوتی', desc: 'پاسخ صوتی برای کم‌سوادان.' },
    ],
  },
  en: {
    kicker: 'Access for everyone',
    title: 'Five channels, one science',
    lead: 'Anyone, on any phone, at any literacy level, reaches the same scientific result.',
    items: [
      { icon: 'globe', title: 'Web & PWA', desc: 'Full dashboard with offline support.' },
      { icon: 'sms', title: 'USSD', desc: 'Works on the simplest phones, no internet.' },
      { icon: 'message', title: 'SMS', desc: 'Text-based queries and alerts.' },
      {
        icon: 'bot',
        title: 'Messaging bots',
        desc: 'Telegram, Eitaa, Bale and Rubika — always by your side.',
      },
      { icon: 'mic', title: 'Voice assistant', desc: 'Spoken answers for low-literacy users.' },
    ],
  },
} as const;

export type ChannelsLang = 'fa' | 'en';
