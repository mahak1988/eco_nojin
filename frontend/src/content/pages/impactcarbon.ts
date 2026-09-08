/** Impact + Carbon page content — honest skeletons: metrics are defined,
 * numbers arrive with the pilot (no invented figures). */

export interface ImpactMetric {
  name: string;
  desc: string;
  unit: string;
}

export interface ImpactContent {
  kicker: string;
  title: string;
  lead: string;
  metricsTitle: string;
  metricsNote: string;
  metrics: ImpactMetric[];
  methodTitle: string;
  methodBody: string;
}

export const impact = {
  fa: {
    kicker: 'تأثیر',
    title: 'تأثیر قابل اندازه‌گیری',
    lead: 'ادعا نمی‌کنیم؛ اندازه می‌گیریم. متریک‌های تأثیر از روز نخست تعریف شده‌اند و پس از پایلوت، همین صفحه زنده می‌شود.',
    metricsTitle: 'متریک‌های تعریف‌شده',
    metricsNote: 'هر متریک با ترکیب پایش ماهواره‌ای و دادهٔ میدانی سنجیده می‌شود؛ انتشار با آغاز پایلوت آغاز می‌شود.',
    metrics: [
      { name: 'هکتار زیر پایش', desc: 'مساحت زمین‌های تحت پایش ماهواره‌ای مستمر', unit: 'هکتار' },
      { name: 'کشاورز آموزش‌دیده', desc: 'کشاورزانی که از کانال‌های پنج‌گانه آموزش دیده‌اند', unit: 'نفر' },
      { name: 'اعتبار کربن صادرشده', desc: 'اعتبارهای تأییدشده و ثبت‌شده روی رجیستری', unit: 'اعتبار' },
      { name: 'بهبود شاخص پوشش گیاهی', desc: 'تغییر NDVI قبل/بعد در زمین‌های برنامهٔ احیا', unit: 'ΔNDVI' },
      { name: 'صرفه‌جویی آب', desc: 'کاهش مصرف با توصیهٔ آبیاری مبتنی بر FAO-56', unit: 'مترمکعب' },
    ],
    methodTitle: 'روش سنجش',
    methodBody:
      'هر متریک با ترکیب دادهٔ سنتینل-۲، اقلیم ERA5 و ثبت میدانی KoBo محاسبه و در گزارش MRV شفاف منتشر می‌شود؛ اعداد ساختگی در این پلتفرم جایی ندارد.',
  },
  en: {
    kicker: 'Impact',
    title: 'Measurable impact',
    lead: 'We do not claim — we measure. Impact metrics are defined from day one, and this page goes live with the pilot.',
    metricsTitle: 'Defined metrics',
    metricsNote: 'Each metric combines Sentinel imagery with field data; publishing starts with the pilot.',
    metrics: [
      { name: 'Hectares under monitoring', desc: 'Land area under continuous satellite monitoring', unit: 'ha' },
      { name: 'Farmers trained', desc: 'Farmers reached through the five access channels', unit: 'people' },
      { name: 'Carbon credits issued', desc: 'Verified credits registered on the registry', unit: 'credits' },
      { name: 'Vegetation index improvement', desc: 'Before/after NDVI change in restoration fields', unit: 'ΔNDVI' },
      { name: 'Water saved', desc: 'Reduced use via FAO-56-based irrigation advice', unit: 'm³' },
    ],
    methodTitle: 'Measurement method',
    methodBody:
      'Every metric is computed from Sentinel-2 data, ERA5 climate and KoBo field records, published in transparent MRV reports. Made-up numbers have no place on this platform.',
  },
} satisfies Record<'fa' | 'en', ImpactContent>;

export interface CarbonContent {
  kicker: string;
  title: string;
  lead: string;
  howTitle: string;
  how: { title: string; desc: string }[];
  participateTitle: string;
  participate: string[];
  statusTitle: string;
  statusBody: string;
}

export const carbon = {
  fa: {
    kicker: 'پروژه‌های کربن',
    title: 'رجیستری کربن، از مزرعه تا بلاکچین',
    lead: 'مسیر اعتبار کربن اکو نوژین، شفاف و مرحله‌به‌مرحله است؛ نقشهٔ پروژه‌های فعال با نخستین پایلوت زنده می‌شود.',
    howTitle: 'مسیر اعتبار کربن',
    how: [
      { title: 'ثبت زمین', desc: 'کشاورز زمین و اقدام حفاظتی را ثبت می‌کند.' },
      { title: 'اندازه‌گیری', desc: 'پایش ماهواره‌ای + ثبت میدانی KoBo.' },
      { title: 'تأیید', desc: 'محاسبهٔ مدل‌محور و راستی‌آزمایی گزارش MRV.' },
      { title: 'ثبت و فروش', desc: 'اعتبار با تأیید بلاکچین روی پالیگون ثبت می‌شود.' },
    ],
    participateTitle: 'چگونه مشارکت کنم؟',
    participate: [
      'کشاورز: زمین خود را برای پایلوت ثبت کنید.',
      'خریدار/نهاد: گزارش‌های MRV تجمیعی را درخواست دهید.',
      'توسعه‌دهنده: از درگاه API به داده‌های تأییدشده وصل شوید.',
    ],
    statusTitle: 'وضعیت فعلی',
    statusBody:
      'زیرساخت رجیستری و زنجیرهٔ MRV آماده است؛ نخستین پروژه‌ها و نقشهٔ زندهٔ آن‌ها با آغاز پایلوت در همین صفحه منتشر می‌شود.',
  },
  en: {
    kicker: 'Carbon projects',
    title: 'The carbon registry, from farm to blockchain',
    lead: 'The Eco Nojin credit path is transparent and step-by-step; the live project map goes live with the first pilot.',
    howTitle: 'The carbon-credit path',
    how: [
      { title: 'Register land', desc: 'The farmer registers land and conservation actions.' },
      { title: 'Measure', desc: 'Satellite monitoring + KoBo field records.' },
      { title: 'Verify', desc: 'Model-based calculation and MRV report verification.' },
      { title: 'Register & sell', desc: 'Credits are recorded with blockchain verification on Polygon.' },
    ],
    participateTitle: 'How to participate?',
    participate: [
      'Farmer: register your land for the pilot.',
      'Buyer / institution: request aggregated MRV reports.',
      'Developer: connect to verified data through the API gateway.',
    ],
    statusTitle: 'Current status',
    statusBody:
      'The registry infrastructure and MRV chain are ready; the first projects and their live map are published on this page with the pilot launch.',
  },
} satisfies Record<'fa' | 'en', CarbonContent>;
