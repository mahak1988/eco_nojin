import type { SiteContent } from './types';

export interface CapabilitiesContent {
  fa: SiteContent['capabilities'];
  en: SiteContent['capabilities'];
}

export const capabilities = {
  fa: {
    kicker: 'قابلیت‌ها',
    title: 'یک پلتفرم، همهٔ چرخهٔ احیا',
    lead: 'از دیده‌بانی ماهواره‌ای تا اقتصاد روستا؛ هر لایه با مدل علمی پشتیبانی می‌شود.',
    items: [
      {
        icon: 'satellite',
        title: 'پایش ماهواره‌ای',
        desc: 'شاخص‌های NDVI، EVI، SAVI، NDWI و NBR از سنتینل-۲ با اعتبارنامهٔ کوپرنیکوس.',
      },
      {
        icon: 'droplets',
        title: 'مدیریت هوشمند آب',
        desc: 'شبیه‌سازی رطوبت خاک و جریان با مدل‌های ریچاردز، سنت‌ونان و FAO-56.',
      },
      {
        icon: 'sprout',
        title: 'خاک سالم و کربن',
        desc: 'پویایی کربن آلی خاک با مدل روت‌سی و گاه‌شمار تغییرات.',
      },
      {
        icon: 'mountain',
        title: 'فرسایش و حفاظت',
        desc: 'برآورد تلفات خاک با روسل و SWAT برای سناریوهای حفاظتی.',
      },
      {
        icon: 'blocks',
        title: 'کربنِ اثبات‌پذیر',
        desc: 'رجیستری اعتبار کربن با ثبت شبیه‌سازی‌شده روی رجیستری (Polygon testnet/mock).',
      },
      {
        icon: 'store',
        title: 'بازار و معیشت',
        desc: 'بازارگاه، آموزش کشاورز و اکوتوریزم برای رونق روستایی.',
      },
    ],
  },
  en: {
    kicker: 'Capabilities',
    title: 'One platform, the full restoration loop',
    lead: 'From satellite watch to rural economics — every layer is backed by a scientific model.',
    items: [
      {
        icon: 'satellite',
        title: 'Satellite monitoring',
        desc: 'NDVI, EVI, SAVI, NDWI and NBR indices from Sentinel-2 via Copernicus credentials.',
      },
      {
        icon: 'droplets',
        title: 'Smart water management',
        desc: 'Soil moisture and flow simulation with Richards, Saint-Venant and FAO-56.',
      },
      {
        icon: 'sprout',
        title: 'Healthy soil & carbon',
        desc: 'Soil organic carbon dynamics with the RothC model and change timelines.',
      },
      {
        icon: 'mountain',
        title: 'Erosion & conservation',
        desc: 'Soil-loss estimation with RUSLE and SWAT for conservation scenarios.',
      },
      {
        icon: 'blocks',
        title: 'Provable carbon',
        desc: 'Carbon-credit registry with simulated registration on Polygon testnet/mock.',
      },
      {
        icon: 'store',
        title: 'Market & livelihoods',
        desc: 'Marketplace, farmer education and ecotourism for rural prosperity.',
      },
    ],
  },
} as const;

export type CapabilitiesLang = 'fa' | 'en';
