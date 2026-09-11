import type { SiteContent } from './types';

export interface PrivacyContent {
  fa: SiteContent['privacy'];
  en: SiteContent['privacy'];
}

export const privacy = {
  fa: {
    kicker: 'حقوقی',
    title: 'حریم خصوصی',
    lead: 'چه داده‌ای جمع می‌کنیم، چرا، و چه حقوقی دارید؛ به‌طور خلاصه و شفاف.',
    version: 'v1.0',
    changelog: ['v1.0 — شهریور ۱۴۰۵: انتشار نسخهٔ نخست'],
    updated: 'شهریور ۱۴۰۵',
    draftNote:
      'این متن نسخهٔ نخست است و پیش از عرضهٔ عمومی خدمات، توسط مشاور حقوقی و متن‌بازِ کمیسیون‌های حفاظت داده بازبینی می‌شود.',
    sections: [
      {
        title: 'اصل کوتاهی داده',
        body: [
          'فقط داده‌ای را جمع می‌کنیم که برای ارائهٔ خدمات لازم است؛ نه بیشتر. جمع‌آوری عمده‌داده و ردیابی تبلیغاتی در طراحی پلتفرم جایی ندارد.',
        ],
      },
      {
        title: 'داده‌هایی که گردآوری می‌کنیم',
        body: [
          'حساب کاربری: ایمیل و — در صورت نیاز به خدمات مالی — اطلاعات هویتی برای احراز هویت (KYC).',
          'پایش و مزرعه: داده‌های میدانی و مشخصات زمینی که خودتان ثبت می‌کنید (فرم‌های KoBo، پروفایل خاک، مرز مزرعه).',
          'فنی: لاگ‌های نرخ و امنیت برای پایداری سرویس. ترجیحات: انتخاب زبان فقط در localStorage مرورگر خودتان ذخیره می‌شود.',
        ],
      },
      {
        title: 'اهداف پردازش',
        body: [
          'ارائهٔ خدمات (پایش، شبیه‌سازی، بازارگاه، آموزش)، تولید گزارش‌های MRV، تأمین امنیت و بهبود محصول. برای هدف دیگر، بدون اطلاع و رضایت، استفاده نمی‌شود.',
        ],
      },
      {
        title: 'نگهداری و امنیت',
        body: [
          'داده‌ها روی زیرساخت Supabase (PostgreSQL) با سیاست‌های سطح ردیف (RLS) نگهداری می‌شود؛ احراز هویت با JWT، محدودسازی نرخ و کنترل دسترسی تقویت شده است.',
        ],
      },
      {
        title: 'اشتراک‌گذاری',
        body: [
          'دادهٔ شما فروخته نمی‌شود. اشتراک‌گذاری فقط با ارائه‌دهندگان زیرساخت ضروری و — برای اقتصاد کربن — گزارش تجمیعی و تأییدشده به خریدار اعتبار، محدود می‌شود.',
        ],
      },
      {
        title: 'کوکی و ذخیره‌سازی محلی',
        body: [
          'این وب‌سایت از ردیاب تبلیغاتی و کوکی شخص ثالث استفاده نمی‌کند؛ تنها انتخاب زبان در حافظهٔ مرورگر شما (localStorage) ذخیره می‌شود.',
        ],
      },
      {
        title: 'حقوق شما',
        body: [
          'حق دسترسی، تصحیح و حذف داده (تا حد مجاز قانونی) دارید. درخواست را به info@econojin.org بفرستید؛ در بازهٔ معقول پاسخ می‌دهیم.',
          'چارچوب مرجع ما الزامات سبک GDPR و قوانین حفاظت دادهٔ حوزه‌های قضایی عملیاتی است؛ انتقال بین‌مرزی داده نیز تابع همین قواعد انجام می‌شود.',
        ],
      },
      {
        title: 'تماس',
        body: ['هر پرسشی دربارهٔ حریم خصوصی: info@econojin.org'],
      },
    ],
  },
  en: {
    kicker: 'Legal',
    title: 'Privacy Policy',
    lead: 'What data we collect, why, and your rights — short and transparent.',
    version: 'v1.0',
    changelog: ['v1.0 — September 2026: initial release'],
    updated: 'September 2026',
    draftNote:
      'This is the first version; it will be reviewed by legal counsel against data-protection requirements before general availability.',
    sections: [
      {
        title: 'Data minimization first',
        body: [
          'We collect only the data required to provide the services — nothing more. Bulk collection and advertising trackers have no place in the platform’s design.',
        ],
      },
      {
        title: 'What we collect',
        body: [
          'Account: email and — only for financial services — identity information for KYC.',
          'Monitoring & farm: the field data you submit yourself (KoBo forms, soil profiles, field boundaries).',
          'Technical: rate and security logs for service stability. Preferences: your language choice is stored only in your browser’s localStorage.',
        ],
      },
      {
        title: 'Purposes of processing',
        body: [
          'Providing services (monitoring, simulation, marketplace, education), producing MRV reports, security, and product improvement. Data is never used for another purpose without notice and consent.',
        ],
      },
      {
        title: 'Storage and security',
        body: [
          'Data is stored on Supabase (PostgreSQL) infrastructure with row-level security (RLS) policies, reinforced by JWT authentication, rate limiting and access controls.',
        ],
      },
      {
        title: 'Sharing',
        body: [
          'Your data is never sold. Sharing is limited to essential infrastructure providers and — for the carbon economy — verified aggregated reports to credit buyers.',
        ],
      },
      {
        title: 'Cookies and local storage',
        body: [
          'This website uses no advertising trackers or third-party cookies; only your language choice is kept in your browser’s localStorage.',
        ],
      },
      {
        title: 'Your rights',
        body: [
          'You have the right to access, correct and delete your data (to the extent legally permitted). Send requests to info@econojin.org; we answer within a reasonable time.',
          'Our reference framework is GDPR-style requirements plus the data-protection laws of operating jurisdictions; cross-border transfers follow the same rules.',
        ],
      },
      {
        title: 'Contact',
        body: ['Any privacy question: info@econojin.org'],
      },
    ],
  },
} as const;

export type PrivacyLang = 'fa' | 'en';
