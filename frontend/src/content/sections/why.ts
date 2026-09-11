import type { SiteContent } from './types';

export interface WhyContent {
  fa: SiteContent['why'];
  en: SiteContent['why'];
}

export const why = {
  fa: {
    kicker: 'چرا اکو نوژین',
    title: 'سه تمایز که جای دیگر پیدا نمی‌کنید',
    items: [
      {
        icon: 'flask',
        title: 'علم قطعی، نه تخمین',
        desc: 'مدل‌های فیزیکی بنیادی — از ریچاردز تا روت‌سی — روی هستهٔ عددی C++ اجرا می‌شوند؛ خروجی در «درجهٔ تصمیم» است، نه صرفاً یک داشبورد.',
      },
      {
        icon: 'globe',
        title: 'عدالت در دسترسی',
        desc: 'از گوشی ساده با USSD تا داشبورد کامل وب؛ پنج کانال و چهارده زبان یعنی هیچ کشاورزی بیرون نمی‌ماند.',
      },
      {
        icon: 'blocks',
        title: 'اثرِ قابل اثبات',
        desc: 'از اندازه‌گیری ماهواره‌ای تا ثبت کربن روی بلاکچین؛ هر ادعا قابل راستی‌آزمایی است.',
      },
    ],
  },
  en: {
    kicker: 'Why Eco Nojin',
    title: 'Three differentiators you won’t find elsewhere',
    items: [
      {
        icon: 'flask',
        title: 'Deterministic science, not guesswork',
        desc: 'Fundamental physical models — Richards to RothC — run on a C++ numerical core; outputs are decision-grade, not just a dashboard.',
      },
      {
        icon: 'globe',
        title: 'Equitable access',
        desc: 'From USSD on basic phones to the full web dashboard; five channels and fourteen languages leave no farmer behind.',
      },
      {
        icon: 'blocks',
        title: 'Provable impact',
        desc: 'From satellite measurement to blockchain-registered carbon; every claim is verifiable.',
      },
    ],
  },
} as const;

export type WhyLang = 'fa' | 'en';
