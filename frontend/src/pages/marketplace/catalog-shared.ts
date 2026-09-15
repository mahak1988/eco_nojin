import type { MarketplaceCategory } from '../../lib/marketplaceTypes';

export const CATEGORY_CONFIG: Record<MarketplaceCategory, { icon: string; labelFa: string; labelEn: string }> = {
  grains: { icon: '🌾', labelFa: 'غلات', labelEn: 'Grains' },
  fruits: { icon: '🍎', labelFa: 'میوه‌ها', labelEn: 'Fruits' },
  vegetables: { icon: '🥬', labelFa: 'سبزیجات', labelEn: 'Vegetables' },
  dairy: { icon: '🥛', labelFa: 'شیر و محصولات پروتئینی', labelEn: 'Dairy' },
  meat: { icon: '🥩', labelFa: 'گوشت', labelEn: 'Meat' },
  spices: { icon: '🫙', labelFa: 'ادویه', labelEn: 'Spices' },
  handicraft: { icon: '🧶', labelFa: 'محصولات دست‌ساز', labelEn: 'Handicraft' },
  village: { icon: '🏘️', labelFa: 'محصولات روستایی', labelEn: 'Village' },
  other: { icon: '📦', labelFa: 'سایر', labelEn: 'Other' },
};

export const SECTION_CONFIG: Record<string, { titleFa: string; titleEn: string; categories: MarketplaceCategory[] }> = {
  featured: { titleFa: 'محصولات برگزیده', titleEn: 'Featured', categories: ['grains', 'fruits', 'vegetables', 'dairy', 'meat', 'spices'] },
  artisan: { titleFa: 'محصولات دست‌ساز و روستایی', titleEn: 'Artisan & Village', categories: ['handicraft', 'village'] },
  other: { titleFa: 'سایر محصولات', titleEn: 'Other', categories: ['other'] },
};

export const ORDER_STATUS_LABEL: Record<string, { fa: string; en: string }> = {
  pending: { fa: 'در انتظار', en: 'Pending' },
  paid: { fa: 'پرداخت شده', en: 'Paid' },
  shipped: { fa: 'ارسال شده', en: 'Shipped' },
  delivered: { fa: 'تحویل شده', en: 'Delivered' },
  cancelled: { fa: 'لغو شده', en: 'Cancelled' },
};

export const PAYMENT_STATUS_LABEL: Record<string, { fa: string; en: string }> = {
  pending: { fa: 'در انتظار', en: 'Pending' },
  paid: { fa: 'پرداخت شده', en: 'Paid' },
  refunded: { fa: 'بازپس گرفته شده', en: 'Refunded' },
};