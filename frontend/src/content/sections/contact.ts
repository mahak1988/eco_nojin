import type { SiteContent } from './types';

export interface ContactContent {
  fa: SiteContent['contact'];
  en: SiteContent['contact'];
}

export const contact = {
  fa: {
    kicker: 'تماس',
    title: 'با ما در تماس باشید',
    lead: 'برای پایلوت، همکاری پژوهشی، سرمایه‌گذاری اثرگذار یا هر پرسشی — فرم را پر کنید یا مستقیم ایمیل بزنید.',
    formTitle: 'فرم پیام',
    formNote:
      'در فاز نخست، ارسال از طریق برنامهٔ ایمیل شما انجام می‌شود (بدون ذخیرهٔ داده در سرور)؛ endpoint اختصاصی بعداً اضافه می‌شود.',
    nameLabel: 'نام',
    emailLabel: 'ایمیل',
    roleLabel: 'نقش شما',
    roles: ['کشاورز / بهره‌بردار', 'پژوهشگر', 'نهاد توسعه / NGO', 'سرمایه‌گذار', 'سایر'],
    messageLabel: 'پیام',
    sendButton: 'ارسال با ایمیل',
    validationError: 'لطفاً نام، ایمیل معتبر و پیام را کامل کنید.',
    successTitle: 'پیام شما ثبت شد',
    successNote: 'به‌محض امکان، پاسخ به ایمیل شما می‌رود.',
    errorTitle: 'ارسال ناموفق بود',
    errorFallback: 'ارسال با ایمیل (روش جایگزین)',
    faqLink: 'پرسش‌های متداول را ببینید',
    emailCardTitle: 'ایمیل مستقیم',
    channelsTitle: 'کانال‌های پیام‌رسان',
    channelsNote:
      'ربات‌های تلگرام، ایتا، بله و روبیکا پس از انتشار عمومی پلتفرم از همین صفحه در دسترس خواهند بود.',
  },
  en: {
    kicker: 'Contact',
    title: 'Get in touch',
    lead: 'For pilots, research partnerships, impact investment or any question — fill the form or email us directly.',
    formTitle: 'Message form',
    formNote:
      'In this first phase, submission happens through your email client (no data stored on a server); a dedicated backend endpoint will be added later.',
    nameLabel: 'Name',
    emailLabel: 'Email',
    roleLabel: 'Your role',
    roles: ['Farmer / producer', 'Researcher', 'Development institution / NGO', 'Impact investor', 'Other'],
    messageLabel: 'Message',
    sendButton: 'Send via email',
    validationError: 'Please complete your name, a valid email and the message.',
    successTitle: 'Your message was received',
    successNote: 'We will reply to your email as soon as possible.',
    errorTitle: 'Submission failed',
    errorFallback: 'Send via email (fallback)',
    faqLink: 'See the FAQ',
    emailCardTitle: 'Direct email',
    channelsTitle: 'Messaging channels',
    channelsNote:
      'The Telegram, Eitaa, Bale and Rubika bots will be available on this page once the platform’s public launch happens.',
  },
} as const;

export type ContactLang = 'fa' | 'en';
