import type { SiteContent } from './types';

export interface TransparencyContent {
  fa: SiteContent['transparency'];
  en: SiteContent['transparency'];
}

export const transparency = {
  fa: {
    kicker: 'شفافیت',
    title: 'شفافیت و گزارش‌ها',
    lead: 'ادعای «اثبات‌پذیری» ما فقط برای کربن نیست؛ پیشرفت پروژه هم باید قابل ردیابی باشد.',
    phasesTitle: 'گاه‌شمار فازهای توسعه',
    phasesNote:
      'بر اساس اسناد فازبندی پروژه (docs/fa)؛ شرح کامل هر فاز در مستندات داخلی نگهداری می‌شود.',
    phases: [
      { id: '۰', title: 'زیرساخت پایه', desc: 'راه‌اندازی مخزن، معماری و چارچوب کیفیت.' },
      { id: '۱', title: 'دادهٔ واقعی', desc: 'سنتینل با CDSE و اقلیم ERA5.' },
      { id: '۲', title: 'زنجیرهٔ علمی', desc: 'به‌کارگیری مدل‌های هیدروما در یک زنجیره.' },
      { id: '۳', title: 'زنجیرهٔ کاربری', desc: 'فرانت‌اند، شبیه‌سازها و داشبورد زنده.' },
      { id: '۴', title: 'کربن و MRV', desc: 'کوبو، گزارش و دادهٔ آزمایشگاهی.' },
      { id: '۵', title: 'اقتصاد', desc: 'لایهٔ اقتصاد و مشوق‌ها.' },
      { id: '۶', title: 'پلتفرم کاربری', desc: 'احراز هویت، نقشه، بازارگاه و آموزش.' },
      { id: '۷', title: 'حسابرسی', desc: 'اعتبارها و کنترل کیفیت.' },
      { id: '۸', title: 'یکپارچه‌سازی', desc: 'شبیه‌سازها، امنیت، OGC و دستیار هوشمند.' },
    ],
    verificationTitle: 'زنجیرهٔ راستی‌آزمایی',
    verification: [
      'اندازه‌گیری: ترکیب پایش ماهواره‌ای سنتینل با دادهٔ میدانی KoBo.',
      'محاسبه: مدل‌های فیزیکی قطعی روی هستهٔ عددی C++.',
       'ثبت: اعتبار کربن با ثبت شبیه‌سازی‌شده روی رجیستری (Polygon testnet/mock).',
      'گزارش: MRV شفاف برای خریداران و نهادهای توسعه.',
    ],
    commitmentsTitle: 'تعهدات ما (ماده ۳ بیانیه)',
    commitments: [
      'راستی‌آزمایی: تمام پروژه‌های احیا با سنجش‌ازدور، پایش زمینی و ممیزی مستقل راستی‌آزمایی و گزارش دوره‌ای آن منتشر می‌شود.',
      'توزیع عادلانه: حداقل ۵۰٪ ارزش ناخالص فروش هر اعتبار کربنی به جوامع محلی و مجریان اختصاص می‌یابد؛ گزارش سالانه در همین صفحه.',
      'بدون هزینهٔ اولیه: ثبت‌نام و مشارکت اولیه رایگان است و هزینه‌ای برای ضرب یا نگهداری اکوکویین دریافت نمی‌شود.',
      'انطباق: تلاش برای هم‌راستایی با موافقت‌نامه پاریس (ماده ۶)، اصول ICVCM، ISO 14064-2 و SDGs.',
      'رضایت آگاهانهٔ جوامع محلی (FPIC) پیش از اجرای هر پروژه احیا در زمین‌های اجتماعی.',
    ],
    reportsNote:
      'گزارش‌های دوره‌ای عمومی (پیشرفت فازها و آمار) از این صفحه منتشر خواهد شد؛ گزارش نخست همراه با آغاز پایلوت.',
  },
  en: {
    kicker: 'Transparency',
    title: 'Transparency & reports',
    lead: 'Our “provable” claim is not only about carbon; project progress must be traceable too.',
    phasesTitle: 'Development phase timeline',
    phasesNote:
      'Based on the project’s phased documentation (docs/fa); the full description of each phase is kept in the internal docs.',
    phases: [
      { id: '0', title: 'Core infrastructure', desc: 'Repository setup, architecture and the quality framework.' },
      { id: '1', title: 'Real data', desc: 'Sentinel via CDSE and ERA5 climate.' },
      { id: '2', title: 'Scientific chain', desc: 'HyDroMa models wired into one chain.' },
      { id: '3', title: 'User-facing chain', desc: 'Frontend chain, simulators and a live dashboard.' },
      { id: '4', title: 'Carbon & MRV', desc: 'KoBo, reporting and lab data.' },
      { id: '5', title: 'Economy', desc: 'The economics layer and incentives.' },
      { id: '6', title: 'User platform', desc: 'Auth, map, marketplace and education.' },
      { id: '7', title: 'Audit', desc: 'Credits and quality control.' },
      { id: '8', title: 'Integration', desc: 'Simulators, security, OGC and the AI assistant.' },
    ],
    verificationTitle: 'The verification chain',
    verification: [
      'Measurement: Sentinel satellite monitoring combined with KoBo field data.',
      'Computation: deterministic physical models on the C++ numerical core.',
       'Registration: carbon credits recorded with simulated registration on Polygon testnet/mock.',
      'Reporting: transparent MRV for buyers and development institutions.',
    ],
    commitmentsTitle: 'Our commitments (Article 3 of the declaration)',
    commitments: [
      'Verification: every restoration project is verified through remote sensing, ground monitoring and independent audit, with periodic reports published.',
      'Fair distribution: at least 50% of the gross value of each carbon credit goes to local communities and implementers; annual report on this page.',
      'No upfront cost: registration and initial participation are free; no fee is charged for minting or holding Eco Coins.',
      'Compliance: we pursue alignment with the Paris Agreement (Article 6), ICVCM principles, ISO 14064-2 and the SDGs.',
      'Free, prior and informed consent (FPIC) of local communities before any restoration project on communal lands.',
    ],
    reportsNote:
      'Periodic public reports (phase progress and stats) will be published on this page; the first one ships with the pilot launch.',
  },
} as const;

export type TransparencyLang = 'fa' | 'en';
