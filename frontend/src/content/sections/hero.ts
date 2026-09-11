import type { SiteContent } from './types';

export interface HeroContent {
  fa: SiteContent['hero'];
  en: SiteContent['hero'];
}

export const hero = {
  fa: {
    kicker: 'پلتفرم علمی اکو نوژین',
    title: 'از دادهٔ ماهواره‌ای تا',
    titleAccent: 'تصمیمِ میدانی',
    subtitle:
      'اکو نوژین با موتور علمی «هیدروما» و پایش ماهواره‌ای سنتینل، شبیه‌سازی‌های تصمیم‌ساز برای آب، خاک، کربن و معیشت روستایی فراهم می‌کند؛ آن‌هم در پنج کانال دسترسی، از وب تا پیام‌رسان.',
    ctaPrimary: 'کاوش پلتفرم',
    ctaSecondary: 'علم پشتِ پروژه',
    visualCaption: 'تصویرسازیِ مفهومی از پایش پوشش گیاهی',
    chips: {
      ndvi: 'NDVI — پوشش گیاهی',
      era5: 'ERA5 — اقلیم',
      soc: 'SOC — کربن آلی خاک',
    },
  },
  en: {
    kicker: 'The Eco Nojin scientific platform',
    title: 'From satellite data to',
    titleAccent: 'field decisions',
    subtitle:
      'Eco Nojin pairs the HyDroMa scientific engine with Sentinel satellite monitoring to deliver decision-grade simulations for water, soil, carbon and rural livelihoods — across five access channels, from web to messaging apps.',
    ctaPrimary: 'Explore the platform',
    ctaSecondary: 'The science behind it',
    visualCaption: 'Conceptual illustration of vegetation monitoring',
    chips: {
      ndvi: 'NDVI — vegetation',
      era5: 'ERA5 — climate',
      soc: 'SOC — soil organic carbon',
    },
  },
} as const;

export type HeroLang = 'fa' | 'en';
