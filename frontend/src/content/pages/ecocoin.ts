/** Eco Coin page content — two-phase framework (G1) with the G2 issuance
 * chain and honest status. No offering claims before G3 (report 64). */

export interface ChainStep {
  title: string;
  desc: string;
}

export interface EcoCoinContent {
  kicker: string;
  title: string;
  lead: string;
  phasesTitle: string;
  phases: { tag: string; title: string; desc: string; status: string }[];
  chainTitle: string;
  chainLead: string;
  chain: ChainStep[];
  commitmentsTitle: string;
  commitments: string[];
  gateTitle: string;
  gateBody: string;
}

export const ecoCoin = {
  fa: {
    kicker: 'اکوکویین',
    title: 'اکوکویین — اعتبارِ احیا',
    lead: 'واحد دیجیتال اعتبار اکو نوژین؛ در دو فازِ شفاف تعریف می‌شود: امروز ابزار مشارکت، فردا اعتبار کربنیِ راستی‌آزمایی‌شده.',
    phasesTitle: 'دو فاز، دو وعدهٔ شفاف',
    phases: [
      {
        tag: 'فاز ۱ — فعال',
        title: 'اعتبار کاربردی',
        desc: 'امروز اکوکویین توکن کاربردی است: پاداشِ اقدام واقعی (کاشت، احیا، پایش) و کلید دسترسی به خدمات پلتفرم. بدون فروش، بدون وعدهٔ سود.',
        status: 'فعال',
      },
      {
        tag: 'فاز ۲ — پس از راستی‌آزمایی مستقل',
        title: 'اعتبار کربنی',
        desc: 'در فاز دوم، اعتبار معادل یک تن دی‌اکسیدکربن ترسیب‌شده تعریف می‌شود؛ اما فقط پس از پیش‌راستی‌آزمایی شبیه‌سازی‌شده مطابق ISO 14064-2 (pre-verification) و تأیید نهاد اعتبارسنج مستقل (VVB — pre-confirmed) صادر و در رجیستری (شبیه‌سازی) ثبت می‌شود.',
        status: 'پیش‌راستی‌آزمایی',
      },
    ],
    chainTitle: 'زنجیرهٔ صدور اعتبار',
    chainLead: 'هیچ اعتباری از هوا بیرون نمی‌آید؛ مسیر هر اعتبار، پنج دروازهٔ سخت‌گیرانه دارد.',
    chain: [
      { title: 'متدولوژی', desc: 'ثبت عمومی روش‌شناسی مطابق اصول ICVCM و ISO 14064-2 (پیش‌راستی‌آزمایی): baseline، additionality، permanence، leakage.' },
      { title: 'کمّی‌سازی', desc: 'محاسبه با موتور هیدروما و دادهٔ سنتینل/ERA5/میدانی.' },
      { title: 'اعتبارسنجی مستقل', desc: 'تأیید توسط نهاد مستقل (VVB) — نه خود پلتفرم.' },
      { title: 'ثبت در رجیستری', desc: 'شناسهٔ یکتا و جلوگیری از احتساب دوگانه (ماده ۶ پاریس).' },
      { title: 'انتشار عمومی', desc: 'گزارش هر اعتبار در صفحهٔ شفافیت.' },
    ],
    commitmentsTitle: 'تعهدات ما',
    commitments: [
      'حداقل ۵۰٪ ارزش ناخالص فروش هر اعتبار به جوامع محلی و مجریان می‌رسد؛ گزارش سالانه در شفافیت.',
      'ثبت‌نام و مشارکت اولیه رایگان است؛ هزینه‌ای برای ضرب یا نگهداری از کاربر گرفته نمی‌شود.',
      'اکوکویینِ حساب شما، دارایی دیجیتال شماست؛ انتقال با رضایت شما و توقیف فقط با دستور قضایی معتبر.',
      'هم‌راستایی با موافقت‌نامه پاریس (ماده ۶) و SDGs.',
    ],
    gateTitle: 'چرا هنوز «عرضه» نکرده‌ایم؟',
    gateBody:
      'چون وعدهٔ عرضه بدون راستی‌آزمایی مستقل و اظهارنظر حقوقی، سبزشویی است. طبق رویهٔ اعلام‌شده (گزارش ۶۴)، عرضهٔ اعتبار کربنی فقط پس از اظهارنظر حقوقی مستقل در هر حوزهٔ قضایی اعلام می‌شود. صبر ما، اعتماد شماست.',
  },
  en: {
    kicker: 'Eco Coin',
    title: 'Eco Coin — the credit of restoration',
    lead: 'The digital credit unit of Eco Nojin, defined in two transparent phases: today a participation instrument, tomorrow a verified carbon credit.',
    phasesTitle: 'Two phases, two transparent promises',
    phases: [
      {
        tag: 'Phase 1 — active',
        title: 'Utility credit',
        desc: 'Today Eco Coin is a utility token: the reward for real action (planting, restoration, monitoring) and the key to platform services. No sales, no profit promises.',
        status: 'Active',
      },
      {
        tag: 'Phase 2 — after independent verification',
        title: 'Carbon credit',
        desc: 'In phase two, the credit equals one tonne of sequestered CO2 — but it is issued and registered only after pre-verification per ISO 14064-2 (pre-verification) and confirmation by an independent validation body (VVB — pre-confirmed).',
        status: 'Pre-verification',
      },
    ],
    chainTitle: 'The issuance chain',
    chainLead: 'No credit appears out of thin air; every credit passes five strict gates.',
    chain: [
      { title: 'Methodology', desc: 'Public registration of the methodology per ICVCM principles and ISO 14064-2 (pre-verification): baseline, additionality, permanence, leakage.' },
      { title: 'Quantification', desc: 'Computed by the HyDroMa engine with Sentinel/ERA5/field data.' },
      { title: 'Independent validation', desc: 'Confirmed by an independent body (VVB) — not by the platform itself.' },
      { title: 'Registry entry', desc: 'A unique ID and double-counting safeguards (Paris Article 6).' },
      { title: 'Public publication', desc: 'Every credit’s report on the transparency page.' },
    ],
    commitmentsTitle: 'Our commitments',
    commitments: [
      'At least 50% of every credit’s gross value reaches local communities and implementers; annual report on transparency.',
      'Registration and initial participation are free; no fee for minting or holding.',
      'Eco Coins in your account are your digital asset; transfer with your consent, freezing only by valid court order.',
      'Alignment with the Paris Agreement (Article 6) and the SDGs.',
    ],
    gateTitle: 'Why haven’t we “offered” yet?',
    gateBody:
      'Because an offering promise without independent verification and legal opinion is greenwashing. Per our declared procedure (report 64), carbon-credit offerings will only be announced after an independent legal opinion in each jurisdiction. Our patience is your trust.',
  },
} satisfies Record<'fa' | 'en', EcoCoinContent>;
