/** Marketplace + Resources page content — honest previews: structure and
 * participation paths now, live data with the pilot. */

export interface MarketplaceContent {
  kicker: string;
  title: string;
  lead: string;
  featuresTitle: string;
  features: { title: string; desc: string }[];
  howTitle: string;
  how: string[];
  statusTitle: string;
  statusBody: string;
}

export const marketplace = {
  fa: {
    kicker: 'بازارگاه',
    title: 'بازارگاه محلی اکو نوژین',
    lead: 'پیوند تولید کشاورز به بازار؛ با قیمت شفاف و عرضهٔ محلی — پس از پایلوت.',
    featuresTitle: 'چه چیزی ارائه می‌شود؟',
    features: [
      { title: 'ویترین محصولات محلی', desc: 'عرضهٔ مستقیم محصول کشاورز بدون واسطهٔ اضافه.' },
      { title: 'روند قیمت‌ها', desc: 'دنبال‌کردن قیمت محصولات در منطقهٔ شما.' },
      { title: 'اتصال به خریدار', desc: 'دیدن تقاضا و مذاکرهٔ مستقیم.' },
    ],
    howTitle: 'مسیر فروشنده و خریدار',
    how: [
      'فروشنده: با ثبت‌نام در پلتفرم، محصول و قیمت پیشنهادی را ثبت می‌کند.',
      'خریدار: محصولات منطقه‌ای را می‌بیند و درخواست می‌دهد.',
      'معامله و تسویه با پشتیبانی پلتفرم و ثبت در پروفایل اکوکیف.',
    ],
    statusTitle: 'وضعیت فعلی',
    statusBody: 'سرویس بازارگاه در معماری پلتفرم آماده است؛ فعال‌سازی عمومی پس از پایلوت و تعیین منطق قیمت‌گذاری محلی انجام می‌شود. برای اطلاع از شروع، خبرنامه را دنبال کنید.',
  },
  en: {
    kicker: 'Marketplace',
    title: 'The Eco Nojin local marketplace',
    lead: 'Linking farmer production to the market — with transparent prices and local supply, after the pilot.',
    featuresTitle: 'What will it offer?',
    features: [
      { title: 'Local product listings', desc: 'Farmers sell directly, without extra middlemen.' },
      { title: 'Price trends', desc: 'Track crop prices in your region.' },
      { title: 'Buyer connection', desc: 'See demand and negotiate directly.' },
    ],
    howTitle: 'Seller and buyer path',
    how: [
      'Seller: register on the platform and list products with an asking price.',
      'Buyer: browse regional products and place requests.',
      'Deal and settlement with platform support, recorded in the EcoWallet profile.',
    ],
    statusTitle: 'Current status',
    statusBody: 'The marketplace service is built into the platform architecture; public activation follows the pilot and local pricing decisions. Follow the newsletter for the launch.',
  },
} satisfies Record<'fa' | 'en', MarketplaceContent>;

export interface ResourcesContent {
  kicker: string;
  title: string;
  lead: string;
  categoriesTitle: string;
  categories: { title: string; desc: string; status: string }[];
  contributeTitle: string;
  contributeBody: string;
}

export const resources = {
  fa: {
    kicker: 'منابع',
    title: 'مرکز منابع دانش',
    lead: 'مستندات، داده و آموزش — به‌تدریج و به‌صورت باز منتشر می‌شود.',
    categoriesTitle: 'دسته‌های منبع',
    categories: [
      { title: 'مستندات فنی', desc: 'معماری، مدل‌ها و استانداردهای پروژه (دوزبانه).', status: 'در حال آماده‌سازی نسخهٔ عمومی' },
      { title: 'داده‌های باز', desc: 'خروجی‌های منتشرشدنی سنجش‌ازدور و اقلیم برای پژوهش.', status: 'با سیاست دادهٔ باز، پس از پایلوت' },
      { title: 'مقالات و ارجاع‌ها', desc: 'ارجاع مدل‌های استاندارد (FAO-56، روسل، روت‌سی و…) و پژوهش‌های همکار.', status: 'در حال گردآوری' },
      { title: 'آموزش کشاورز', desc: 'محتوای LMS به زبان‌های محلی.', status: 'پس از انتشار پلتفرم' },
    ],
    contributeTitle: 'مشارکت در منابع',
    contributeBody: 'مستند یا داده‌ای دارید که به این مرکز اضافه شود؟ از صفحهٔ تماس با نقش پژوهشگر پیشنهاد دهید — پروژه متن‌باز است و مشارکت بخشی از فرهنگ ما.',
  },
  en: {
    kicker: 'Resources',
    title: 'The knowledge hub',
    lead: 'Docs, data and training — published progressively and openly.',
    categoriesTitle: 'Resource categories',
    categories: [
      { title: 'Technical documentation', desc: 'Project architecture, models and standards (bilingual).', status: 'Public version in preparation' },
      { title: 'Open data', desc: 'Publishable remote-sensing and climate outputs for research.', status: 'With the open-data policy, after the pilot' },
      { title: 'Papers & references', desc: 'References for the standard models (FAO-56, RUSLE, RothC…) and partner research.', status: 'Being collected' },
      { title: 'Farmer training', desc: 'LMS content in local languages.', status: 'After platform launch' },
    ],
    contributeTitle: 'Contribute resources',
    contributeBody: 'Have a document or dataset for this hub? Propose it via the contact page with the researcher role — the project is open source and contribution is part of our culture.',
  },
} satisfies Record<'fa' | 'en', ResourcesContent>;
