import type { SiteContent } from './types';

export interface TermsContent {
  fa: SiteContent['terms'];
  en: SiteContent['terms'];
}

export const terms = {
  fa: {
    kicker: 'حقوقی',
    title: 'شرایط استفاده',
    lead: 'قواعد استفاده از وب‌سایت و خدمات اکو نوژین؛ لطفاً پیش از استفاده بخوانید.',
    version: 'v1.0',
    changelog: ['v1.0 — شهریور ۱۴۰۵: انتشار نسخهٔ نخست'],
    updated: 'شهریور ۱۴۰۵',
    draftNote:
      'این متن نسخهٔ نخست است و پیش از عرضهٔ عمومی خدمات، توسط مشاور حقوقی بازبینی و کامل می‌شود.',
    sections: [
      {
        title: 'پذیرش شرایط',
        body: [
          'با دسترسی به وب‌سایت یا استفاده از خدمات اکو نوژین، این شرایط را می‌پذیرید. اگر با هر بخش از آن موافق نیستید، لطفاً از خدمات استفاده نکنید.',
        ],
      },
      {
        title: 'توصیف خدمات',
        body: [
          'اکو نوژین پلتفرمی علمی برای احیای اکوسیستم، کشاورزی هوشمند، مدیریت آب و خاک و اقتصاد کربن است. این وب‌سایت اطلاعات عمومی پروژه را ارائه می‌دهد؛ خدمات کاربردی (پایش، شبیه‌سازی، بازارگاه و آموزش) از طریق درگاه یکپارچهٔ API عرضه می‌شوند.',
        ],
      },
      {
        title: 'ماهیت اطلاعاتی خروجی‌ها',
        body: [
          'خروجی‌های شبیه‌سازی و پایش، «ابزار تصمیم‌یار» هستند و توصیهٔ قطعی فنی، مالی یا حقوقی محسوب نمی‌شوند. مسئولیت تصمیم نهایی در مزرعه و میدان با کاربر یا متخصص اوست.',
        ],
      },
      {
        title: 'حساب کاربری و استفادهٔ مجاز',
        body: [
          'برای خدمات کاربردی به حساب کاربری نیاز است. اطلاعات حساب باید دقیق و به‌روز باشد و حفاظت از اعتبارنامه‌ها بر عهدهٔ شماست.',
          'دسترسی غیرمجاز، دور زدن محدودیت نرخ، اسکرپ خودکار و هرگونه سوءاستفاده از درگاه API مجاز نیست.',
        ],
      },
      {
        title: 'مالکیت فکری',
        body: [
          'کد منبع پروژه با مجوز MIT منتشر می‌شود. نام، نشان و محتوای وب‌سایت متعلق به اکو نوژین است. استفاده از داده‌های ماهواره‌ای تابع شرایط کوپرنیکوس (CDSE) است.',
        ],
      },
      {
        title: 'خدمات مالی و اکوکویین',
        body: [
          'اکوکویین واحد دیجیتال اعتبار اکو نوژین است و در دو فاز تعریف می‌شود: فاز یک (فعلی) — توکن کاربردی برای دسترسی به خدمات پلتفرم؛ فاز دو — اعتبار کربنی معادل یک تن دی‌اکسیدکربن ترسیب‌شده، که فقط پس از پیش‌راستی‌آزمایی شبیه‌سازی‌شده مطابق ISO 14064-2 (pre-verification) و تأیید نهاد اعتبارسنج مستقل (VVB — pre-confirmed) صادر و در رجیستری (شبیه‌سازی) ثبت می‌شود.',
          'در هیچ فاز، اکوکویین فروش توکن، وعدهٔ سود یا محصول سرمایه‌گذاری نیست؛ در صورت تحقق شرایط حقوقی و مجوزها، عرضهٔ اعتبار کربنی تابع اظهارنظر حقوقی مستقل خواهد بود و پلتفرم تسهیل‌گر است، نه نگهدارندهٔ وجوه.',
          'اکوکویینِ ذخیره‌شده در حساب کاربر، دارایی دیجیتال اوست؛ انتقال داوطلبانه با رضایت کاربر انجام می‌شود و توقیف یا مسدودسازی تنها بر اساس دستور قضایی/اداری معتبر و الزامات مبارزه با پول‌شویی (AML) انجام می‌گیرد.',
          'حداقل ۵۰ درصد ارزش ناخالص فروش هر اعتبار کربنی، به جوامع محلی و مجریان پروژه‌های احیا اختصاص می‌یابد و گزارش سالانهٔ آن در صفحهٔ شفافیت منتشر می‌شود.',
          'پلتفرم در پی هم‌راستایی با موافقت‌نامه پاریس (ماده ۶)، اصول ICVCM، ISO 14064-2 و اهداف توسعه پایدار (SDGs) است؛ انطباق نهایی تابع مجوزهای هر حوزهٔ قضایی است.',
        ],
      },
      {
        title: 'سلب مسئولیت',
        body: [
          'خدمات «همان‌گونه که هست» ارائه می‌شوند. صحت داده‌های ماهواره‌ای و اقلیمی تابع منابع بیرونی است و وقفهٔ سرویس ممکن است. تا حد مجاز قانون، مسئولیتی برای خسارات غیرمستقیم ناشی از اتکای صرف به خروجی‌ها پذیرفته نمی‌شود.',
        ],
      },
      {
        title: 'تغییر شرایط',
        body: [
          'این شرایط ممکن است به‌روز شود؛ نسخهٔ جدید با تغییر شمارهٔ نسخه و تاریخِ آخرین بازنگری در همین صفحه منتشر می‌شود و ادامهٔ استفاده به معنای پذیرش آن است.',
        ],
      },
      {
        title: 'تماس و حل اختلاف',
        body: [
          'برای هر پرسش یا اختلاف، نخست با info@econojin.org در تماس باشید تا حل مسالمت‌آمیز در اولویت باشد. تبعات قانونی تابع قوانین حوزه‌های قضایی عملیاتی پلتفرم است.',
        ],
      },
    ],
  },
  en: {
    kicker: 'Legal',
    title: 'Terms of Use',
    lead: 'The rules for using the Eco Nojin website and services; please read before using them.',
    version: 'v1.0',
    changelog: ['v1.0 — September 2026: initial release'],
    updated: 'September 2026',
    draftNote:
      'This is the first version; it will be reviewed and completed by legal counsel before general availability.',
    sections: [
      {
        title: 'Acceptance of terms',
        body: [
          'By accessing the website or using Eco Nojin services, you accept these terms. If you disagree with any part, please do not use the services.',
        ],
      },
      {
        title: 'Description of services',
        body: [
          'Eco Nojin is a scientific platform for ecosystem restoration, smart agriculture, water and soil management, and the carbon economy. This website presents general project information; operational services (monitoring, simulation, marketplace, education) are delivered through the unified API gateway.',
        ],
      },
      {
        title: 'Informational nature of outputs',
        body: [
          'Simulation and monitoring outputs are decision-support tools, not definitive technical, financial or legal advice. Responsibility for final field decisions rests with the user or their specialist.',
        ],
      },
      {
        title: 'Accounts and permitted use',
        body: [
          'Operational services require an account. Account information must be accurate and up to date, and you are responsible for safeguarding your credentials.',
          'Unauthorized access, circumventing rate limits, automated scraping and any API misuse are prohibited.',
        ],
      },
      {
        title: 'Intellectual property',
        body: [
          'The project source code is released under the MIT License. The Eco Nojin name, mark and website content belong to Eco Nojin. Satellite data use is subject to Copernicus (CDSE) terms.',
        ],
      },
      {
        title: 'Financial services and Eco Coin',
        body: [
          'Eco Coin is the digital credit unit of Eco Nojin, defined in two phases: phase one (current) — a utility token for accessing platform services; phase two — a carbon credit equivalent to one tonne of sequestered CO2, issued and registered only after pre-verification per ISO 14064-2 (pre-verification) and confirmation by an independent validation body (VVB — pre-confirmed).',
          'In neither phase is Eco Coin a token sale, a profit promise or an investment product; if legal conditions and licenses are met, offering carbon credits will follow an independent legal opinion, and the platform facilitates rather than holds funds.',
          'Eco Coins stored in a user’s account are that user’s digital asset; voluntary transfer happens with the user’s consent, and freezing or blocking occurs only under valid judicial/administrative orders and anti-money-laundering (AML) obligations.',
 'At least 50% of the gross value of every carbon credit is allocated directly to local communities and restoration project implementers, with an annual report published on the transparency page.',
          'The platform seeks alignment with the Paris Agreement (Article 6), the ICVCM Core Carbon Principles, ISO 14064-2 and the Sustainable Development Goals (SDGs); final compliance follows the licenses of each jurisdiction.',
        ],
      },
      {
        title: 'Disclaimer',
        body: [
          'Services are provided “as is”. The accuracy of satellite and climate data depends on external sources, and service interruptions may occur. To the extent permitted by law, no liability is accepted for indirect damages arising from sole reliance on outputs.',
        ],
      },
      {
        title: 'Changes to terms',
        body: [
          'These terms may be updated; the new version is published on this page with a changed version number and “last reviewed” date, and continued use constitutes acceptance.',
        ],
      },
      {
        title: 'Contact and disputes',
        body: [
          'For any question or dispute, contact info@econojin.org first; amicable resolution comes first. Legal matters follow the laws of the jurisdictions where the platform operates.',
        ],
      },
    ],
  },
} as const;

export type TermsLang = 'fa' | 'en';
