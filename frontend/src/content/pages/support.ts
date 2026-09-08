/** Support page content (bilingual). USSD/SMS facts from docs/fa/03: SMS
 * keywords SOIL, CROP, PRICE, WEATHER, ASK; USSD for feature phones. */

export interface SupportGuide {
  title: string;
  steps: string[];
}

export interface SupportContent {
  kicker: string;
  title: string;
  lead: string;
  guidesTitle: string;
  ussd: SupportGuide;
  sms: SupportGuide;
  voice: SupportGuide;
  troubleshootingTitle: string;
  troubleshooting: { q: string; a: string }[];
  moreTitle: string;
  moreBody: string;
}

export const support = {
  fa: {
    kicker: 'پشتیبانی',
    title: 'راهنمای گام‌به‌گام',
    lead: 'از گوشی ساده تا داشبورد کامل؛ هر کانال، راهنمای خودش را دارد.',
    guidesTitle: 'راهنمای کانال‌ها',
    ussd: {
      title: 'USSD — بدون اینترنت',
      steps: [
        'کد USSD پلتفرم را در برنامهٔ شماره‌گیری گوشی وارد و تماس بگیرید.',
        'منوی متنی روی صفحهٔ گوشی باز می‌شود؛ با اعداد گزینه‌ها را انتخاب کنید.',
        'گزارش خواسته‌شده (خاک، محصول، قیمت…) روی همان صفحه نمایش داده می‌شود.',
        'هیچ اینترنت و نصبی لازم نیست؛ روی ساده‌ترین گوشی‌ها کار می‌کند.',
      ],
    },
    sms: {
      title: 'SMS — با کلیدواژه',
      steps: [
        'به شمارهٔ سرویس پیامک پلتفرم پیام بدهید و یکی از کلیدواژه‌ها را بنویسید.',
        'SOIL — وضعیت خاک | CROP — وضعیت محصول | PRICE — قیمت بازار.',
        'WEATHER — هواشناسی مزرعه | ASK — پرسش آزاد از دستیار.',
        'پاسخ به‌صورت پیامک متنی برمی‌گردد.',
      ],
    },
    voice: {
      title: 'دستیار صوتی',
      steps: [
        'از منوی تماس، گزینهٔ دستیار صوتی را انتخاب کنید.',
        'پرسش خود را به زبان خودتان بگویید.',
        'پاسخ صوتی پخش می‌شود — برای کم‌سوادان طراحی شده است.',
      ],
    },
    troubleshootingTitle: 'رفع اشکال رایج',
    troubleshooting: [
      { q: 'پاسخی دریافت نکردم', a: 'یک بار دیگر درخواست بدهید؛ اگر تکرار شد، از صفحهٔ تماس با ذکر کانال و ساعت گزارش دهید.' },
      { q: 'پیامک نمی‌رسد', a: 'حافظهٔ پیامک را خالی و شمارهٔ سرویس را مسدود نبودن بررسی کنید.' },
      { q: 'منوی USSD باز نمی‌شود', a: 'برخی اپراتورها سشنامهٔ USSD را محدود می‌کنند؛ چند دقیقه بعد تلاش کنید.' },
    ],
    moreTitle: 'بیشتر از این',
    moreBody: 'آموزش‌های تصویری و انجمن کاربران با انتشار عمومی پلتفرم اضافه می‌شوند؛ پرسش‌های فنی را از صفحهٔ تماس بپرسید.',
  },
  en: {
    kicker: 'Support',
    title: 'Step-by-step guides',
    lead: 'From a basic phone to the full dashboard — every channel has its own guide.',
    guidesTitle: 'Channel guides',
    ussd: {
      title: 'USSD — no internet',
      steps: [
        'Dial the platform’s USSD code from the phone app.',
        'A text menu opens on the screen; pick options with numbers.',
        'The requested report (soil, crop, price…) shows on the same screen.',
        'No internet and no install — works on the simplest phones.',
      ],
    },
    sms: {
      title: 'SMS — by keyword',
      steps: [
        'Text one of the keywords to the platform’s SMS service number.',
        'SOIL — soil status | CROP — crop status | PRICE — market prices.',
        'WEATHER — farm weather | ASK — free question to the assistant.',
        'The answer comes back as a text message.',
      ],
    },
    voice: {
      title: 'Voice assistant',
      steps: [
        'Pick the voice assistant option from the call menu.',
        'Ask your question in your own language.',
        'The answer is played as audio — designed for low-literacy users.',
      ],
    },
    troubleshootingTitle: 'Common troubleshooting',
    troubleshooting: [
      { q: 'I got no answer', a: 'Retry once; if it repeats, report the channel and time via the contact page.' },
      { q: 'SMS does not arrive', a: 'Clear your message inbox and make sure the service number is not blocked.' },
      { q: 'USSD menu does not open', a: 'Some operators throttle USSD sessions; try again in a few minutes.' },
    ],
    moreTitle: 'More to come',
    moreBody: 'Video tutorials and a user forum arrive with the public launch; technical questions go through the contact page.',
  },
} satisfies Record<'fa' | 'en', SupportContent>;
