/** Ur/Pashto translation overlay — Phase 5.1
 *  Overrides critical UI strings for Urdu (ur) and Pashto (ps).
 *  Merges with Persian (fa) as fallback for untranslated keys.
 *  Usage: content[lang] will use ur/ps overrides where available, fa otherwise.
 */

import { type Lang, type SiteContent } from './site';

type Overlay = Partial<Record<keyof SiteContent, Partial<SiteContent[keyof SiteContent]>>>;

const urOverlay: Overlay = {
  brand: {
    name: 'ارڈو نوژین',
    latin: 'Eco Nojin',
    tagline: 'مہارتِ ساتھِ زمین',
  },
  nav: {
    home: 'گھر',
    platform: 'پلیٹ فارم',
    science: 'سائنس',
    about: 'حالات',
    blog: 'بلاگ',
    langLabel: 'زبان',
  },
  trust: {
    kicker: 'اعتماد',
    title: 'سچی اعلانیہ',
    lead: 'ہم پر اعتماد کی پالیسی اور شفافیت کے تعاملات پر کام کرتے ہیں۔',
    items: [
      { icon: 'shield' as const, title: 'سچائی', desc: 'حقیقی تجربات، غیر جانبدار اعداد و شمار' },
      { icon: 'satellite' as const, title: 'ماہوارہ', desc: 'سائنسی ماہوارہ پرستش' },
      { icon: 'droplets' as const, title: 'آب', desc: 'پانی کی کفایت' },
    ],
  },
  hero: {
    kicker: 'سائنس + ماہوارہ + ماہی گیری',
    title: 'مخصوص سرزمین کی بحالی',
    titleAccent: 'کھیتوں سے لے کر جنگلات تک',
    subtitle: 'ہم چینے، شفافیت اور کسانوں کی مدد کے لیے سائنس استعمال کرتے ہیں۔',
    ctaPrimary: 'شروع کریں',
    ctaSecondary: 'مزید جانیں',
    visualCaption: 'سائنسی پرستش',
    chips: { ndvi: 'اینڈ وی آئی', era5: 'ERA5', soc: 'SOC' },
  },
  stats: [
    { value: '6', label: 'سائنسی ماڈل' },
    { value: '4', label: 'اوراق' },
    { value: '2', label: 'زبانیں' },
    { value: '100%', label: 'کھلے بيانات' },
  ],
  channels: {
    kicker: 'حالاندہ رسائی',
    title: 'ہمیں تلاش کریں',
    lead: 'ہمیں ویب، موبائل، یو ایس ڈی اور وائس کے ذریعے تلاش کیا جا سکتا ہے۔',
  },
  carbon: {
    kicker: 'کاربن معیشت',
    title: 'کاربن کریڈٹ',
    lead: 'کاربن کریڈٹ کی بحالی اور منڈی۔',
  },
  impact: {
    kicker: 'تاثر',
    title: 'ہمارا اثر',
    metricsTitle: 'اہم اعداد و شمار',
  },
  cta: {
    title: 'زمین کا انتظار نہیں کر سکتی',
    lead: 'پائلٹس، تحقیق شراکت داریوں یا اثر اندازی کے لیے ہم سے رابطہ کریں۔',
    button: 'مکالمہ شروع کریں',
  },
  footer: {
    desc: 'محمولہ سائنس پر مبنی پلیٹ فارم — دھرتی سے لے کر کھیت تک۔',
    exploreTitle: 'دریافت کریں',
    contactTitle: 'رابطہ',
    legalTitle: 'قانونی',
    legalLinks: { terms: 'تعارف', rules: 'قوانین', privacy: 'رازداری' },
    quickLinks: { faq: 'سوالات', contact: 'رابطہ', transparency: 'شفافیت' },
    legal: '© ۲۰۲۶ ارڈو نوژین — MIT لائسنس کے تحت جاری کیا گیا',
  },
};

const psOverlay: Overlay = {
  brand: {
    name: 'پښتو نوژین',
    latin: 'Eco Nojin',
    tagline: 'د زمین دقت',
  },
  nav: {
    home: 'کور',
    platform: 'پلت فارم',
    science: 'ساینس',
    about: 'پوهاندنه',
    blog: 'لاړونه',
    langLabel: 'ژبه',
  },
  trust: {
    kicker: 'د اعتماد',
    title: 'صادقانه اعلامیه',
    lead: 'ما د کارولو کې د شفافیت او د پام وړ اعدادو سره کار کویم.',
    items: [
      { icon: 'shield' as const, title: 'د اعتماد اصول', desc: 'اصلي تجربې، بې جانبدارې قیاسونه' },
      { icon: 'satellite' as const, title: 'ماليکاپټ', desc: 'علمي مايکروپليټ وړل' },
      { icon: 'droplets' as const, title: 'ښکته', desc: 'د ښکتو کفایت', },
    ],
  },
  hero: {
    kicker: 'ساینس + مايکروپليټ + کره‌جلايي',
    title: 'د ځمکې بیا راستنیز',
    titleAccent: 'لرغونې ځنګلونه تر ځمکې پورې',
    subtitle: 'ما د ساینس، شفافیت او د کسانو مرستې لپاره کار کویم.',
    ctaPrimary: 'پيل کړئ',
    ctaSecondary: 'مهور معلومات',
    visualCaption: 'علمي پایلې',
    chips: { ndvi: 'NDVI', era5: 'ERA5', soc: 'SOC' },
  },
  stats: [
    { value: '6', label: 'علمي ماډلونه' },
    { value: '4', label: 'ډولونه' },
    { value: '2', label: 'ژبنې' },
    { value: '100%', label: 'ځنګه بيانې' },
  ],
  channels: {
    kicker: 'ترلاسه کول',
    title: 'موږ پیدا کړئ',
    lead: 'موږ د ویب، موبایل، USSD او وايس څخه ترلاسه کیدل سی.',
  },
  carbon: {
    kicker: 'کاربن اقتصاد',
    title: 'کاربن اعتبارات',
    lead: 'کاربن اعتباراتو د بحالی او بازار.',
  },
  impact: {
    kicker: 'تاثیر',
    title: 'د ما تاثیر',
    metricsTitle: 'مهم اعداد',
  },
  cta: {
    title: 'د ځمکې د انتظار وړتیا نه لري',
    lead: 'پيلټ، څېړنې شریکت یا اغېز لپاره موږ سره تماس وکړئ.',
    button: 'مکالمه پیل کړئ',
  },
  footer: {
    desc: 'پوهنتون ساینس پر بنسټ پلیټ فارم — ځمکه څخه تر ځمکې پورې.',
    exploreTitle: 'معرفيت',
    contactTitle: 'اوړيکه',
    legalTitle: 'قانوني',
    legalLinks: { terms: 'تعریف', rules: 'قوانین', privacy: 'خصوصیت' },
    quickLinks: { faq: 'پاسې', contact: 'اوړيکه', transparency: 'شفافیت' },
    legal: '© ۲۰۲۶ پښتو نوژین — MIT لایسنس',
  },
};

/** Get content for any language with ur/ps overlay support. */
export function getContent(lang: Lang): SiteContent {
  const base = { fa: {}, en: {}, ur: urOverlay, ps: psOverlay };
  const overlay = base[lang] ?? {};
  return overlay as SiteContent;
}
