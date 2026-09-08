/** Partners + Careers page content (bilingual skeletons with CTAs). */

export interface PartnersContent {
  kicker: string;
  title: string;
  lead: string;
  whoTitle: string;
  who: { title: string; desc: string }[];
  modelsTitle: string;
  models: { title: string; desc: string }[];
  ctaTitle: string;
  ctaBody: string;
}

export const partners = {
  fa: {
    kicker: 'شرکا',
    title: 'با هم، در مقیاس اکوسیستم',
    lead: 'احیای اکوسیستم کار یک نهاد نیست؛ شبکه‌ای از دانشگاه‌ها، NGOها، اپراتورها و نهادهای توسعه لازم است.',
    whoTitle: 'به دنبال چه همکارانی هستیم؟',
    who: [
      { title: 'دانشگاه‌ها و مراکز پژوهشی', desc: 'اعتبارسنجی علمی مدل‌ها و هم‌انتشاری.' },
      { title: 'NGOها و نهادهای توسعه', desc: 'اجرای میدانی پایلوت و توانمندسازی جوامع محلی.' },
      { title: 'اپراتورهای مخابراتی', desc: 'کانال‌های USSD/SMS پایدار برای روستاها.' },
      { title: 'شرکت‌های AgTech', desc: 'یکپارچه‌سازی از طریق درگاه API.' },
    ],
    modelsTitle: 'مدل‌های همکاری',
    models: [
      { title: 'پایلوت مشترک', desc: 'اجرای آزمایشی منطقه‌ای با داده و گزارش مشترک.' },
      { title: 'پژوهش مشترک', desc: 'دسترسی به مدل‌ها و داده برای پژوهش داوری‌شده.' },
      { title: 'توزیع و دسترسی', desc: 'رساندن کانال‌های پنج‌گانه به جوامع محلی.' },
    ],
    ctaTitle: 'گفت‌وگو را شروع کنیم',
    ctaBody: 'از صفحهٔ تماس با نقش «سایر» یا «نهاد توسعه» پیام دهید؛ برنامهٔ همکاری اختصاصی می‌فرستیم.',
  },
  en: {
    kicker: 'Partners',
    title: 'Together, at ecosystem scale',
    lead: 'Ecosystem restoration is not one organization’s job — it needs a network of universities, NGOs, telcos and development institutions.',
    whoTitle: 'Which partners are we looking for?',
    who: [
      { title: 'Universities & research centers', desc: 'Scientific validation of models and co-publication.' },
      { title: 'NGOs & development institutions', desc: 'Field pilots and local community empowerment.' },
      { title: 'Telecom operators', desc: 'Reliable USSD/SMS channels for rural areas.' },
      { title: 'AgTech companies', desc: 'Integration through the API gateway.' },
    ],
    modelsTitle: 'Partnership models',
    models: [
      { title: 'Joint pilot', desc: 'A regional trial with shared data and reporting.' },
      { title: 'Joint research', desc: 'Access to models and data for peer-reviewed research.' },
      { title: 'Distribution & access', desc: 'Bringing the five channels to local communities.' },
    ],
    ctaTitle: 'Let’s start the conversation',
    ctaBody: 'Message us via the contact page with the role “Other” or “Development institution”; we send a tailored partnership plan.',
  },
} satisfies Record<'fa' | 'en', PartnersContent>;

export interface CareersContent {
  kicker: string;
  title: string;
  lead: string;
  valuesTitle: string;
  values: { title: string; desc: string }[];
  rolesTitle: string;
  roles: string[];
  openTitle: string;
  openBody: string;
}

export const careers = {
  fa: {
    kicker: 'فرصت‌های همکاری',
    title: 'به تیم بپیوندید',
    lead: 'تیمی کوچک و متمرکز که علم و فناوری را به مزرعه می‌رساند؛ رشد ما سریع است و فرهنگ ما صداقت فنی.',
    valuesTitle: 'ارزش‌های ما',
    values: [
      { title: 'صداقت فنی', desc: 'عدد جعلی و ادعای بی‌مبنا جایگاهی ندارد.' },
      { title: 'دسترسی عادلانه', desc: 'محصول برای ضعیف‌ترین اتصال طراحی می‌شود.' },
      { title: 'علمِ باز', desc: 'کد و روش، متن‌باز و قابل راستی‌آزمایی.' },
    ],
    rolesTitle: 'حوزه‌هایی که همیشه به آن‌ها نیاز داریم',
    roles: [
      'مهندس بک‌اند (FastAPI/PostgreSQL)',
      'متخصص یادگیری ماشین و سنجش‌ازدور',
      'مهندس GIS و نقشه‌برداری',
      'توسعه‌دهندهٔ موبایل/PWA',
      'کارشناس پیوند میان‌رشته‌ای کشاورزی و جامعه',
    ],
    openTitle: 'موقعیت‌های باز',
    openBody: 'موقعیت‌های رسمی با انتشار عمومی اعلام می‌شوند؛ از همین حالا می‌توانید رزومه و حوزهٔ علاقه را از صفحهٔ تماس بفرستید.',
  },
  en: {
    kicker: 'Careers',
    title: 'Join the team',
    lead: 'A small, focused team taking science and technology to the field; we grow fast and our culture is technical honesty.',
    valuesTitle: 'Our values',
    values: [
      { title: 'Technical honesty', desc: 'No made-up numbers, no unsupported claims.' },
      { title: 'Equitable access', desc: 'The product is designed for the weakest connection.' },
      { title: 'Open science', desc: 'Code and methods are open source and verifiable.' },
    ],
    rolesTitle: 'Skills we always need',
    roles: [
      'Backend engineer (FastAPI/PostgreSQL)',
      'ML & remote-sensing specialist',
      'GIS engineer',
      'Mobile/PWA developer',
      'Agriculture–community liaison',
    ],
    openTitle: 'Open positions',
    openBody: 'Formal openings are announced at public launch; meanwhile, send your CV and area of interest via the contact page.',
  },
} satisfies Record<'fa' | 'en', CareersContent>;
