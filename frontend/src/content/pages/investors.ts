/** Investors page content — public-safe summary of INVESTOR_PITCH.md
 * (no confidential figures on the public site; deck is provided on request). */

export interface InvestorsContent {
  kicker: string;
  title: string;
  lead: string;
  problemTitle: string;
  problem: { title: string; desc: string }[];
  solutionTitle: string;
  solution: string[];
  statusTitle: string;
  status: string[];
  roundTitle: string;
  roundBody: string;
  deckCta: string;
}

export const investors = {
  fa: {
    kicker: 'برای سرمایه‌گذاران',
    title: 'فرصتی در مقیاس ۲.۵ میلیارد کشاورز',
    lead: 'اکو نوژین علم کشاورزی را به بازاری می‌رساند که تا امروز از ابزار دیجیتال محروم بوده است.',
    problemTitle: 'مسئله',
    problem: [
      { title: '۲.۵ میلیارد کشاورز خرد', desc: 'بزرگ‌ترین بازارِ کم‌برخوردار جهان.' },
      { title: '۷۰٪ بدون ابزار دیجیتال', desc: 'پلتفرم‌های موجود به گوشی هوشمند و سواد دیجیتال تکیه دارند.' },
      { title: '۲۵٪ افت بهره‌وری تا ۲۰۵۰', desc: 'تغییر اقلیم، امنیت غذایی را تهدید می‌کند.' },
    ],
    solutionTitle: 'راه‌حل ما',
    solution: [
      'پنج کانال دسترسی (وب/PWA، USSD، SMS، ربات، صوتی) در چهارده زبان.',
      'موتور علمی هیدروما: مدل‌های فیزیکی قطعی + سنجش‌ازدور + لایهٔ اقتصاد.',
       'اقتصاد کربن با MRV شفاف و رجیستری شبیه‌سازی‌شده.',
      'معماری مونوریپو آمادهٔ مقیاس: ۳۸ میکروسرویس + هستهٔ عددی C++20.',
    ],
    statusTitle: 'وضعیت اجرا',
    status: [
      'فازهای ۰ تا ۸ توسعه مطابق مستندات پروژه طی شده‌اند.',
      'زنجیرهٔ علمی، داشبورد و چرخهٔ MRV کار می‌کنند.',
      'گام بعدی: پایلوت منطقه‌ای با جامعهٔ کشاورزان.',
    ],
    roundTitle: 'دور سرمایه‌گذاری',
    roundBody:
      'در حال حاضر دور Seed فعال است. جزئیات مالی در نسخهٔ عمومی منتشر نمی‌شود؛ برای دریافت Pitch Deck و داده‌های مدل مالی، از صفحهٔ تماس با نقش «سرمایه‌گذار» درخواست دهید.',
    deckCta: 'درخواست Pitch Deck',
  },
  en: {
    kicker: 'For investors',
    title: 'An opportunity at the scale of 2.5 billion farmers',
    lead: 'Eco Nojin takes agricultural science to a market that has been excluded from digital tools.',
    problemTitle: 'The problem',
    problem: [
      { title: '2.5B smallholder farmers', desc: 'The largest underserved market in the world.' },
      { title: '70% without digital tools', desc: 'Existing platforms depend on smartphones and digital literacy.' },
      { title: '25% productivity decline by 2050', desc: 'Climate change threatens food security.' },
    ],
    solutionTitle: 'Our solution',
    solution: [
      'Five access channels (web/PWA, USSD, SMS, bots, voice) in fourteen languages.',
      'The HyDroMa engine: deterministic physical models + remote sensing + an economics layer.',
       'A carbon economy with transparent MRV and a simulated registry.',
      'A scale-ready monorepo: 38 microservices + a C++20 numerical core.',
    ],
    statusTitle: 'Execution status',
    status: [
      'Development phases 0–8 are complete per the project documentation.',
      'The scientific chain, dashboard and MRV loop are working.',
      'Next step: a regional pilot with a farming community.',
    ],
    roundTitle: 'The round',
    roundBody:
      'A Seed round is currently active. Financial details are not published on the public site; request the pitch deck and the financial model via the contact page with the role “Impact investor”.',
    deckCta: 'Request the pitch deck',
  },
} satisfies Record<'fa' | 'en', InvestorsContent>;
