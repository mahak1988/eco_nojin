import type { SiteContent } from './types';

export interface FaqContent {
  fa: SiteContent['faq'];
  en: SiteContent['faq'];
}

export const faq = {
  fa: {
    kicker: 'پرسش‌های متداول',
    title: 'پاسخ پرسش‌های پرتکرار',
    lead: 'هرچه دربارهٔ اکو نوژین، هیدروما و مسیر کربن پرتکرارترین پرسش‌هاست؛ در یک نگاه.',
    categories: ['همه', 'پلتفرم', 'علم', 'کربن', 'دسترسی'],
    items: [
      {
        cat: 'پلتفرم',
        q: 'اکو نوژین دقیقاً چیست؟',
        a: 'یک پلتفرم علمی و بین‌المللی برای احیای اکوسیستم، کشاورزی هوشمند، مدیریت آب و خاک، رونق روستایی، مشوق‌های کربن، بازارگاه و اکوتوریزم — با موتور علمی هیدروما و پایش ماهواره‌ای سنتینل.',
      },
      {
        cat: 'علم',
        q: 'هیدروما چه می‌کند؟',
        a: 'موتور علمی و محاسباتی اکو نوژین است: مدل‌های فیزیکی قطعی (ریچاردز، سنت‌ونان، FAO-56، روسل، SWAT، روت‌سی و…) را با دادهٔ ماهواره‌ای و لایهٔ اقتصاد ترکیب می‌کند تا شبیه‌سازی‌های درجهٔ تصمیم بدهد.',
      },
      {
        cat: 'علم',
        q: 'داده‌ها از کجا می‌آیند؟',
        a: 'تصاویر سنتینل-۲/۱ از کوپرنیکوس (CDSE)، بازتحلیل اقلیمی ERA5، نقشه‌های خاک SoilGrids و داده‌های میدانی که خود کاربران ثبت می‌کنند (فرم‌های KoBo).',
      },
      {
        cat: 'دسترسی',
        q: 'برای کشاورز خرد چه فایده‌ای دارد؟',
        a: 'دسترسی به نتیجهٔ علمی بدون نیاز به دانش تخصصی: توصیهٔ آبیاری، هشدار فرسایش، وضعیت پوشش گیاهی و بازار — به زبان خودش.',
      },
      {
        cat: 'دسترسی',
        q: 'حتماً گوشی هوشمند و اینترنت لازم است؟',
        a: 'نه. علاوه بر وب/PWA، کانال‌های USSD و SMS برای گوشی‌های ساده و اینترنت ضعیف طراحی شده‌اند و دستیار صوتی برای کم‌سوادان.',
      },
      {
        cat: 'کربن',
        q: 'اعتبار کربن چطور تأیید می‌شود؟',
        a: 'اندازه‌گیری با ترکیب پایش ماهواره‌ای و میدانی انجام می‌شود و ثبت اعتبار با تأیید بلاکچین روی پالیگون ثبت می‌گردد؛ گزارش MRV شفاف برای خریداران ارائه می‌شود.',
      },
      {
        cat: 'کربن',
        q: 'آیا اکوکویین یک محصول سرمایه‌گذاری است؟',
        a: 'نه. اکوکویین توکن کاربردی برای دسترسی به خدمات پلتفرم است؛ نه فروش توکن، نه وعدهٔ سود و نه محصول سرمایه‌گذاری.',
      },
      {
        cat: 'علم',
        q: 'خروجی‌های علمی چقدر قابل اعتمادند؟',
        a: 'پایهٔ آن‌ها مدل‌های فیزیکی قطعی و دادهٔ ماهواره‌ای واقعی است؛ اما هر خروجی «ابزار تصمیم‌یار» است، نه توصیهٔ قطعی — تصمیم نهایی با کاربر و متخصص اوست.',
      },
      {
        cat: 'پلتفرم',
        q: 'داده‌های مزرعه‌ام چه می‌شود؟',
        a: 'طبق سیاست حریم خصوصی، فقط دادهٔ لازم جمع می‌شود، فروخته نمی‌شود، روی زیرساخت Supabase با سیاست‌های RLS نگهداری می‌شود و حق دسترسی/تصحیح/حذف دارید.',
      },
      {
        cat: 'دسترسی',
        q: 'چطور در پایلوت مشارکت کنم؟',
        a: 'از صفحهٔ تماس پیام بگذارید یا به info@econojin.org بنویسید؛ نقش خود را (کشاورز، پژوهشگر، نهاد، سرمایه‌گذار) ذکر کنید.',
      },
      {
        cat: 'پلتفرم',
        q: 'سایت به چه زبان‌هایی عرضه می‌شود؟',
        a: 'هم‌اکنون فارسی و انگلیسی؛ پلتفرم برای چهارده زبان طراحی شده و به‌تدریج اضافه می‌شوند.',
      },
      {
        cat: 'پلتفرم',
        q: 'آیا پروژه متن‌باز است؟',
        a: 'بله؛ کد منبع با مجوز MIT منتشر می‌شود.',
      },
    ],
  },
  en: {
    kicker: 'FAQ',
    title: 'Frequently asked questions',
    lead: 'The most common questions about Eco Nojin, HyDroMa and the carbon path — at a glance.',
    categories: ['All', 'Platform', 'Science', 'Carbon', 'Access'],
    items: [
      {
        cat: 'Platform',
        q: 'What exactly is Eco Nojin?',
        a: 'An international scientific platform for ecosystem restoration, smart agriculture, water and soil management, rural prosperity, carbon incentives, a marketplace and ecotourism — powered by the HyDroMa engine and Sentinel satellite monitoring.',
      },
      {
        cat: 'Science',
        q: 'What does HyDroMa do?',
        a: 'It is Eco Nojin’s scientific and computational engine: it combines deterministic physical models (Richards, Saint-Venant, FAO-56, RUSLE, SWAT, RothC and more) with satellite data and an economics layer to deliver decision-grade simulations.',
      },
      {
        cat: 'Science',
        q: 'Where does the data come from?',
        a: 'Sentinel-2/1 imagery from Copernicus (CDSE), the ERA5 climate reanalysis, SoilGrids soil maps, and field data submitted by users themselves (KoBo forms).',
      },
      {
        cat: 'Access',
        q: 'What does a smallholder farmer gain?',
        a: 'Access to scientific results without needing specialized knowledge: irrigation advice, erosion alerts, vegetation status and market info — in their own language.',
      },
      {
        cat: 'Access',
        q: 'Do I need a smartphone and internet?',
        a: 'No. Besides web/PWA, USSD and SMS channels are designed for basic phones and weak connectivity, plus a voice assistant for low-literacy users.',
      },
      {
        cat: 'Carbon',
        q: 'How is a carbon credit verified?',
        a: 'Measurement combines satellite and field monitoring, and credit registration is recorded with blockchain verification on Polygon; transparent MRV reports go to buyers.',
      },
      {
        cat: 'Carbon',
        q: 'Is Eco Coin an investment product?',
        a: 'No. Eco Coin is a utility token for accessing platform services — not a token sale, not a profit promise, not an investment product.',
      },
      {
        cat: 'Science',
        q: 'How reliable are the scientific outputs?',
        a: 'They are grounded in deterministic physical models and real satellite data; still, every output is a decision-support tool, not definitive advice — the final decision rests with the user and their specialist.',
      },
      {
        cat: 'Platform',
        q: 'What happens to my farm data?',
        a: 'Per the privacy policy: only necessary data is collected, it is never sold, it is stored on Supabase with RLS policies, and you have access, correction and deletion rights.',
      },
      {
        cat: 'Access',
        q: 'How can I join the pilot?',
        a: 'Send a message from the contact page or write to info@econojin.org; mention your role (farmer, researcher, institution, investor).',
      },
      {
        cat: 'Platform',
        q: 'Which languages does the site support?',
        a: 'Persian and English today; the platform is designed for fourteen languages and more will be added over time.',
      },
      {
        cat: 'Platform',
        q: 'Is the project open source?',
        a: 'Yes; the source code is released under the MIT License.',
      },
    ],
  },
} as const;

export type FaqLang = 'fa' | 'en';
