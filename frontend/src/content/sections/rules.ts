import type { SiteContent } from './types';

export interface RulesContent {
  fa: SiteContent['rules'];
  en: SiteContent['rules'];
}

export const rules = {
  fa: {
    kicker: 'حقوقی',
    title: 'قوانین و مقررات پلتفرم',
    lead: 'قواعد مشارکت در پلتفرم؛ از ثبت دادهٔ میدانی تا استفاده از ربات‌ها و API.',
    version: 'v1.0',
    changelog: ['v1.0 — شهریور ۱۴۰۵: انتشار نسخهٔ نخست'],
    updated: 'شهریور ۱۴۰۵',
    draftNote:
      'این متن نسخهٔ نخست است و پیش از عرضهٔ عمومی خدمات، توسط مشاور حقوقی بازبینی و کامل می‌شود.',
    sections: [
      {
        title: 'دادهٔ واقعی ثبت کنید',
        body: [
          'داده‌های میدانی و پایش باید واقعی، دقیق و متعلق به زمین شما باشند. دادهٔ نادرست، گزارش‌های MRV و اعتبار کربنِ کل جامعهٔ کاربری را مخدوش می‌کند و جدی‌ترین نقض این قوانین است.',
        ],
      },
      {
        title: 'استفادهٔ منصفانه از API',
        body: [
          'محدودیت نرخ، توکن دسترسی و سهمیه‌ها باید رعایت شوند. اسکرپ، تلاش برای دسترسی غیرمجاز و بارگذاری غیرمعمول ممنوع است.',
        ],
      },
      {
        title: 'محتوای بارگذاری‌شده',
        body: [
          'مالکیت محتوایی که بارگذاری می‌کنید نزد شما می‌ماند؛ اما برای پردازش و نمایش در چارچوب خدمات به اکو نوژین اجازه می‌دهید. انتشار محتوای غیرقانونی، گمراه‌کننده یا متعلق به دیگران بدون اجازه ممنوع است.',
        ],
      },
      {
        title: 'ربات‌ها و کانال‌های پیام‌رسان',
        body: [
          'استفاده از ربات تلگرام، ایتا، بله، روبیکا و کانال‌های USSD/SMS تابع همین قوانین است. سوءاستفاده از ارسال انبوه یا درخواست‌های مصنوعی، محدود یا قطع می‌شود.',
        ],
      },
      {
        title: 'احراز هویت و مبارزه با پول‌شویی',
        body: [
          'برای خدمات مالی (اکوکیف، تسهیل سرمایه‌گذاری و اعتبار کربن)، تکمیل فرایند KYC و رعایت ضوابط AML الزامی است؛ اطلاعات درخواستی فقط برای همین هدف پردازش می‌شود.',
        ],
      },
      {
        title: 'مسئولیت کاربران',
        body: [
          'کاربران از پلتفرم فقط برای اهداف مشروع و در راستای احیای اکوسیستم استفاده می‌کنند.',
          'صحت اطلاعات هویتی و مالی بر عهدهٔ کاربر است.',
          'هرگونه استفاده از اکوکویین برای پول‌شویی، کلاهبرداری یا فعالیت‌های خلاف قوانین ملی و بین‌المللی ممنوع است و پیگرد قانونی خواهد داشت.',
        ],
      },
      {
        title: 'نقض قوانین',
        body: [
          'بسته به شدت نقض، اقدام‌ها از هشدار تا تعلیق موقت یا قطع حساب در پی دارد. گزارش تخلف یا اعتراض را به info@econojin.org بفرستید.',
        ],
      },
      {
        title: 'به‌روزرسانی قوانین',
        body: [
          'قوانین همراه با رشد پلتفرم به‌روز می‌شوند؛ شمارهٔ نسخه و تاریخ آخرین بازنگری در بالای همین صفحه ثبت می‌شود.',
        ],
      },
    ],
  },
  en: {
    kicker: 'Legal',
    title: 'Platform rules & regulations',
    lead: 'Participation rules — from field-data submission to bots and API usage.',
    version: 'v1.0',
    changelog: ['v1.0 — September 2026: initial release'],
    updated: 'September 2026',
    draftNote:
      'This is the first version; it will be reviewed and completed by legal counsel before general availability.',
    sections: [
      {
        title: 'Submit real data',
        body: [
          'Field and monitoring data must be real, accurate and belong to your land. False data corrupts MRV reports and the whole community’s carbon credits — it is the most serious violation of these rules.',
        ],
      },
      {
        title: 'Fair use of the API',
        body: [
          'Respect rate limits, access tokens and quotas. Scraping, unauthorized-access attempts and abnormal load generation are prohibited.',
        ],
      },
      {
        title: 'Uploaded content',
        body: [
          'Ownership of content you upload remains with you; however, you grant Eco Nojin permission to process and display it within the scope of the services. Illegal, misleading or unauthorized third-party content is prohibited.',
        ],
      },
      {
        title: 'Bots and messaging channels',
        body: [
          'Use of the Telegram, Eitaa, Bale and Rubika bots and of USSD/SMS channels follows these same rules. Bulk-spam abuse or artificial request patterns will be limited or cut off.',
        ],
      },
      {
        title: 'KYC and anti-money-laundering',
        body: [
          'For financial services (Eco Coin, investment facilitation and carbon credits), completing KYC and following AML rules is mandatory; requested information is processed only for this purpose.',
        ],
      },
      {
        title: 'User responsibilities',
        body: [
          'Users employ the platform only for lawful purposes aligned with ecosystem restoration.',
          'The accuracy of identity and financial information is the user’s responsibility.',
          'Any use of Eco Coin for money laundering, fraud or activities contrary to national and international laws is prohibited and will be prosecuted.',
        ],
      },
      {
        title: 'Violations',
        body: [
          'Depending on severity, violations lead from warnings to temporary suspension or account termination. Report violations or appeals to info@econojin.org.',
        ],
      },
      {
        title: 'Rule updates',
        body: [
          'Rules evolve with the platform; the version number and last-reviewed date are recorded at the top of this page.',
        ],
      },
    ],
  },
} as const;

export type RulesLang = 'fa' | 'en';
