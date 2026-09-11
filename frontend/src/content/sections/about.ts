import type { SiteContent } from './types';

export interface AboutContent {
  fa: SiteContent['about'];
  en: SiteContent['about'];
}

export const about = {
  fa: {
    kicker: 'دربارهٔ ما',
    title: 'علم، متعلق به همه',
    lead: 'اکو نوژین با این باور ساخته شده که دانش کشاورزی باید به دست همان‌ها برسد که زمین را نگه می‌دارند.',
    paragraphs: [
      'اکو نوژین یک پلتفرم بین‌المللی و مبتنی بر استاندارد برای احیای اکوسیستم، کشاورزی هوشمند، مدیریت آب و خاک، رونق روستایی، حمایت از دامداران، مشوق‌های کربن، بازارگاه و اکوتوریزم است. هیدروما موتور علمی و محاسباتی آن است؛ ترکیبی از مدل‌های فیزیکی قطعی، پایش ماهواره‌ای MRV و لایهٔ اقتصاد و مالی.',
      'هدف ما ساده است: ۲.۵ میلیارد کشاورز خرد جهان که تا امروز از ابزارهای دیجیتال کشاورزی محروم بوده‌اند، بتوانند در پنج کانال و چهارده زبان به نتیجهٔ علمی برسند و از احیای زمین، درآمد بسازند. از علمِ همتایان (peer-reviewed) تا پیام متنی، فاصله باید فقط چند کلیک یا یک پیام باشد.',
    ],
    timelineTitle: 'گاه‌شمار توسعه',
    timelineNote:
      'بر اساس مستندات فازبندی‌شدهٔ پروژه؛ جزئیات هر فاز در اسناد داخلی docs/fa موجود است.',
    timeline: [
      { id: '۰', title: 'فاز ۰ — زیرساخت پایه', desc: 'راه‌اندازی مخزن، معماری، محیط توسعه و چارچوب کیفیت.', status: 'completed' },
      { id: '۱', title: 'فاز ۱ — دادهٔ واقعی', desc: 'اتصال داده‌های واقعی؛ سنتینل با اعتبارنامهٔ CDSE و اقلیم ERA5.', status: 'completed' },
      { id: '۲', title: 'فاز ۲ — زنجیرهٔ علمی', desc: 'به‌کارگیری مدل‌های علمی هیدروما در یک زنجیرهٔ محاسباتی.', status: 'completed' },
      { id: '۳', title: 'فاز ۳ — زنجیرهٔ کاربری', desc: 'زنجیرهٔ فرانت‌اند، هاب شبیه‌سازها و داشبورد زنده.', status: 'active' },
      { id: '۴', title: 'فاز ۴ — کربن و MRV', desc: 'MRV کربن، پایش میدانی کوبو، گزارش و دادهٔ آزمایشگاهی.', status: 'active' },
      { id: '۵', title: 'فاز ۵ — اقتصاد', desc: 'لایهٔ اقتصاد و مالی؛ اکوکیف و مشوق‌ها.', status: 'planned' },
      { id: '۶', title: 'فاز ۶ — پلتفرم کاربری', desc: 'Supabase، احراز هویت، نقشه، بازارگاه، پروفایل و آموزش (LMS).', status: 'planned' },
      { id: '۷', title: 'فاز ۷ — حسابرسی', desc: 'حسابرسی، اعتبارها و کنترل کیفیت.', status: 'planned' },
      { id: '۸', title: 'فاز ۸ — یکپارچه‌سازی', desc: 'یکپارچه‌سازی، شبیه‌سازها، امنیت، OGC و دستیار هوشمند.', status: 'planned' },
    ],
    inviteTitle: 'به ما بپیوندید',
    invite:
      'به‌عنوان کشاورز، پژوهشگر، سرمایه‌گذار اثرگذار یا نهاد توسعه، در پایلوت و رشد پلتفرم شریک شوید.',
    contactTitle: 'تماس',
    contactPageLink: 'رفتن به صفحهٔ تماس',
    emailLabel: 'ایمیل',
    email: 'info@econojin.org',
    siteLabel: 'وب‌سایت',
    site: 'econojin.org',
    licenseLabel: 'مجوز',
    license: 'متن‌باز، MIT',
    legalEntityLabel: 'شخصیت حقوقی',
    legalEntity: 'شرکت کشت و صنعت دشت امید نارون',
    contributingTitle: 'مشارکت در پروژهٔ متن‌باز',
    contributingBody: 'کد منبع با مجوز MIT منتشر می‌شود؛ مستندسازی، تست، ترجمهٔ زبان‌ها و رفع اشکال از مخزن پروژه شروع می‌شود. راهنمای مشارکت همراه مستندات فنی ارائه می‌گردد.',
  },
  en: {
    kicker: 'About us',
    title: 'Science belongs to everyone',
    lead: 'Eco Nojin was built on the belief that agricultural knowledge should reach the very people who steward the land.',
    paragraphs: [
      'Eco Nojin is an international, standards-based platform for ecosystem restoration, smart agriculture, water and soil management, rural prosperity, pastoralist support, carbon incentives, a marketplace and ecotourism. HyDroMa is its scientific and computational engine — a combination of deterministic physical models, satellite-based MRV, and an economics and finance layer.',
      'Our goal is simple: the world’s 2.5 billion smallholder farmers, long excluded from digital AgTech, should reach scientific results in five channels and fourteen languages — and earn from restoring the land. The distance from peer-reviewed science to a text message should be a few taps, or one message.',
    ],
    timelineTitle: 'Development timeline',
    timelineNote:
      'Based on the project’s phased documentation; full details of each phase live in the internal docs.',
    timeline: [
      { id: '0', title: 'Phase 0 — Core infrastructure', desc: 'Repository setup, architecture and the quality framework.', status: 'completed' },
      { id: '1', title: 'Phase 1 — Real data', desc: 'Real data connections; Sentinel via CDSE and ERA5 climate.', status: 'completed' },
      { id: '2', title: 'Phase 2 — Scientific chain', desc: 'HyDroMa models wired into one computational chain.', status: 'completed' },
      { id: '3', title: 'Phase 3 — User-facing chain', desc: 'Frontend chain, simulator hub and live dashboard.', status: 'active' },
      { id: '4', title: 'Phase 4 — Carbon & MRV', desc: 'Carbon MRV, KoBo field monitoring, reports and lab data.', status: 'active' },
      { id: '5', title: 'Phase 5 — Economy', desc: 'The economics layer; EcoWallet and incentives.', status: 'planned' },
      { id: '6', title: 'Phase 6 — User platform', desc: 'Supabase, authentication, map, marketplace, profiles and LMS.', status: 'planned' },
      { id: '7', title: 'Phase 7 — Audit', desc: 'Audits, credits and quality control.', status: 'planned' },
      { id: '8', title: 'Phase 8 — Integration', desc: 'Integration, simulators, security, OGC and the AI assistant.', status: 'planned' },
    ],
    inviteTitle: 'Join us',
    invite:
      'Join the pilot and growth of the platform as a farmer, researcher, impact investor or development institution.',
    contactTitle: 'Contact',
    contactPageLink: 'Go to the contact page',
    emailLabel: 'Email',
    email: 'info@econojin.org',
    siteLabel: 'Website',
    site: 'econojin.org',
    licenseLabel: 'License',
    license: 'Open source, MIT',
    legalEntityLabel: 'Legal entity',
    legalEntity: 'Dasht-e Omid Naroon Agro-Industry Co.',
    contributingTitle: 'Contribute to the open project',
    contributingBody: 'The source code is released under the MIT License; start with documentation, tests, locale translations or bug fixes from the project repository. A contribution guide ships with the technical docs.',
  },
} as const;

export type AboutLang = 'fa' | 'en';
