/** Pilot (Iran) + Academia landing page content (bilingual).
 * Pilot form posts to POST /api/v1/pilot/apply; academia form reuses the
 * contact endpoint with a researcher preset. */

export interface PilotContent {
  kicker: string;
  title: string;
  lead: string;
  offerTitle: string;
  offer: string[];
  eligibilityTitle: string;
  eligibility: string[];
  formTitle: string;
  formNote: string;
  nameLabel: string;
  phoneLabel: string;
  provinceLabel: string;
  hectaresLabel: string;
  cropLabel: string;
  channelLabel: string;
  channels: string[];
  consentLabel: string;
  submitButton: string;
  successTitle: string;
  successNote: string;
  validationError: string;
  timelineTitle: string;
  timelineNote: string;
}

export const pilotIran = {
  fa: {
    kicker: 'پایلوت ایران',
    title: 'پایلوت منطقه‌ای اکو نوژین',
    lead: 'ثبت‌نام علاقه‌مندی برای نخستین پایلوت منطقه‌ای؛ ظرفیت محدود، انتخاب بر اساس زمین و آمادگی.',
    offerTitle: 'پایلوت چه می‌دهد؟',
    offer: [
      'دسترسی زودهنگام به پلتفرم و داشبورد پایش زمین.',
      'آموزش کانال‌های پنج‌گانه برای خود و کارگران مزرعه.',
      'پایش ماهواره‌ای رایگان زمین در دورهٔ پایلوت.',
      'مشارکت در نخستین چرخهٔ اعتبار کربن با گزارش MRV.',
    ],
    eligibilityTitle: 'شرایط شرکت',
    eligibility: [
      'ساکن ایران و دسترسی به زمین کشاورزی (ملک یا اجاره).',
      'گوشی ساده یا هوشمند — هر دو کافی است.',
      'رضایت به ثبت دادهٔ میدانی زمین در دورهٔ پایلوت.',
    ],
    formTitle: 'فرم ثبت علاقه‌مندی',
    formNote: 'این فرم فقط ثبت علاقه‌مندی است؛ پس از بررسی، برای گام بعدی با شما تماس می‌گیریم.',
    nameLabel: 'نام و نام خانوادگی',
    phoneLabel: 'شمارهٔ تماس',
    provinceLabel: 'استان',
    hectaresLabel: 'مساحت زمین (هکتار — اختیاری)',
    cropLabel: 'محصول اصلی (اختیاری)',
    channelLabel: 'کانال مورد علاقه',
    channels: ['وب/PWA', 'USSD', 'SMS', 'ربات پیام‌رسان', 'صوتی'],
    consentLabel: 'با ثبت دادهٔ میدانی زمینم در دورهٔ پایلوت موافقم.',
    submitButton: 'ثبت علاقه‌مندی',
    successTitle: 'ثبت شد',
    successNote: 'علاقه‌مندی شما ثبت شد؛ پس از بازبینی با شما تماس می‌گیریم.',
    validationError: 'نام، شمارهٔ تماس، استان و تأیید رضایت لازم است.',
    timelineTitle: 'زمان‌بندی',
    timelineNote: 'پس از تکمیل ظرفیت هر منطقه، فهرست نهایی پایلوت اعلام می‌شود؛ گزارش پیشرفت در صفحهٔ شفافیت منتشر خواهد شد.',
  },
  en: {
    kicker: 'Iran pilot',
    title: 'The Eco Nojin regional pilot',
    lead: 'Interest registration for the first regional pilot; limited capacity, selected by land and readiness.',
    offerTitle: 'What does the pilot give you?',
    offer: [
      'Early access to the platform and the land-monitoring dashboard.',
      'Training on the five channels for you and your farm workers.',
      'Free satellite monitoring of your land during the pilot.',
      'Participation in the first carbon-credit cycle with an MRV report.',
    ],
    eligibilityTitle: 'Who can join?',
    eligibility: [
      'Based in Iran with access to farmland (owned or leased).',
      'A basic or smart phone — both work.',
      'Consent to record field data on your land during the pilot.',
    ],
    formTitle: 'Interest form',
    formNote: 'This form only records interest; we contact you for the next step after review.',
    nameLabel: 'Full name',
    phoneLabel: 'Phone number',
    provinceLabel: 'Province',
    hectaresLabel: 'Land size (hectares — optional)',
    cropLabel: 'Main crop (optional)',
    channelLabel: 'Preferred channel',
    channels: ['Web/PWA', 'USSD', 'SMS', 'Messaging bot', 'Voice'],
    consentLabel: 'I agree to record my land’s field data during the pilot.',
    submitButton: 'Register interest',
    successTitle: 'Registered',
    successNote: 'Your interest is recorded; we will contact you after review.',
    validationError: 'Name, phone, province and consent are required.',
    timelineTitle: 'Timeline',
    timelineNote: 'Once each region fills up, the final pilot list is announced; progress is published on the transparency page.',
  },
} satisfies Record<'fa' | 'en', PilotContent>;

export interface AcademiaContent {
  kicker: string;
  title: string;
  lead: string;
  modelsTitle: string;
  models: { title: string; desc: string }[];
  provideTitle: string;
  provide: string[];
  formTitle: string;
  formNote: string;
  nameLabel: string;
  emailLabel: string;
  affiliationLabel: string;
  topicLabel: string;
  submitButton: string;
  successTitle: string;
  successNote: string;
  validationError: string;
}

export const academia = {
  fa: {
    kicker: 'دانشگاه‌ها و پژوهش',
    title: 'همکاری پژوهشی با اکو نوژین',
    lead: 'مدل‌های هیدروما و دادهٔ سنجش‌ازدور، بستری برای پژوهش داوری‌شده است؛ بیایید با هم منتشر کنیم.',
    modelsTitle: 'مدل‌های همکاری',
    models: [
      { title: 'پژوهش مشترک', desc: 'دسترسی به خروجی مدل‌ها برای مقاله و پایان‌نامه.' },
      { title: 'اعتبارسنجی علمی', desc: 'بازتولید نتایج و انتشار نقد و مقایسه.' },
      { title: 'پروژهٔ دانشجویی', desc: 'تعریف پروژه‌های کارشناسی/ارشد روی دادهٔ واقعی.' },
    ],
    provideTitle: 'چه چیزی ارائه می‌دهیم؟',
    provide: [
      'دسترسی API به شبیه‌سازی‌ها و شاخص‌های ماهواره‌ای.',
      'هم‌راستایی موضوع پژوهش با نقشهٔ راه فنی.',
      'ذکر نام نهاد شما در صفحهٔ شفافیت و مستندات.',
    ],
    formTitle: 'فرم همکاری پژوهشی',
    formNote: 'درخواست شما مستقیم به تیم پژوهش ارسال می‌شود (از طریق endpoint عمومی تماس، با نقش پژوهشگر).',
    nameLabel: 'نام و نام خانوادگی',
    emailLabel: 'ایمیل دانشگاهی',
    affiliationLabel: 'نهاد / دانشگاه',
    topicLabel: 'موضوع پژوهش پیشنهادی',
    submitButton: 'ارسال درخواست',
    successTitle: 'درخواست ارسال شد',
    successNote: 'تیم پژوهش بررسی می‌کند و پاسخ به ایمیل شما می‌رود.',
    validationError: 'نام، ایمیل معتبر، نهاد و موضوع پژوهش لازم است.',
  },
  en: {
    kicker: 'Universities & research',
    title: 'Research collaboration with Eco Nojin',
    lead: 'HyDroMa models and remote-sensing data are a substrate for peer-reviewed research — let’s publish together.',
    modelsTitle: 'Collaboration models',
    models: [
      { title: 'Joint research', desc: 'Access to model outputs for papers and theses.' },
      { title: 'Scientific validation', desc: 'Reproduce results and publish critiques and comparisons.' },
      { title: 'Student projects', desc: 'BSc/MSc projects defined on real data.' },
    ],
    provideTitle: 'What we provide',
    provide: [
      'API access to simulations and satellite indices.',
      'Alignment of your topic with the technical roadmap.',
      'Your institution credited on the transparency page and docs.',
    ],
    formTitle: 'Research collaboration form',
    formNote: 'Your request goes straight to the research team (through the public contact endpoint, with the researcher role).',
    nameLabel: 'Full name',
    emailLabel: 'Academic email',
    affiliationLabel: 'Institution / university',
    topicLabel: 'Proposed research topic',
    submitButton: 'Send request',
    successTitle: 'Request sent',
    successNote: 'The research team will review it and reply to your email.',
    validationError: 'Name, a valid email, institution and topic are required.',
  },
} satisfies Record<'fa' | 'en', AcademiaContent>;
