import type { SiteContent } from './types';

export interface TrustContent {
  fa: SiteContent['trust'];
  en: SiteContent['trust'];
}

export const trust = {
  fa: {
    kicker: 'اعتماد',
    title: 'دلایلی که به اعتماد ساخته‌اند',
    lead: 'اکو نوژین روی همین اصول ساخته شده؛ هر ادعا قابل راستی‌آزمایی است.',
    items: [
      {
        icon: 'flask',
        title: 'علم قطعی، نه تخمین',
        desc: 'مدل‌های فیزیکی بنیادی — ریچاردز، سنت‌ونان، FAO-56، روت‌سی، SWAT — روی هستهٔ عددی C++20 با pybind11.',
      },
      {
        icon: 'satellite',
        title: 'دادهٔ معتبر',
        desc: 'شاخص‌های پوشش گیاشتی از سنتینل-۲ با اعتبارنامهٔ کوپرنیکوس؛ اقلیم ERA5؛ خاک SoilGrids.',
      },
      {
        icon: 'blocks',
        title: 'کربنی قابل اثبات',
        desc: 'مرجع اعتبار کربن با ثبت شبیه‌سازی‌شده روی رجیستری (Polygon testnet/mock); MRV شفاف برای خریداران.',
      },
      {
        icon: 'shield',
        title: 'متن‌باز و امن',
        desc: 'هستهٔ پلتفرم تحت مجوز MIT منتشر می‌شود؛ رمزنگاری هیبریدی (Kyber + Dilithium) در مسیر.',
      },
    ],
  },
  en: {
    kicker: 'Trust',
    title: 'Why you can rely on this',
    lead: 'Eco Nojin is built on verifiable foundations — every claim is auditable.',
    items: [
      {
        icon: 'flask',
        title: 'Deterministic science, not guesswork',
        desc: 'Fundamental physical models — Richards, Saint-Venant, FAO-56, RothC, SWAT — on a C++20 core via pybind11.',
      },
      {
        icon: 'satellite',
        title: 'Trusted data sources',
        desc: 'Vegetation indices from Sentinel-2 (Copernicus credentials); climate via ERA5; soil data via SoilGrids.',
      },
      {
        icon: 'blocks',
        title: 'Provable carbon',
        desc: 'Carbon-credit registry with simulated registration on Polygon testnet/mock; transparent MRV for buyers.',
      },
      {
        icon: 'shield',
        title: 'Open & secure',
        desc: 'The platform core is released under the MIT License; hybrid PQC (Kyber + Dilithium) is underway.',
      },
    ],
  },
} as const;

export type TrustLang = 'fa' | 'en';
