/** HyDroMa dashboard content — the 12 engineering packages (HP-01..HP-12)
 * from the booklets, bilingual, plus calculator labels. */

export interface PackageSpec {
  code: string;
  title: string;
  desc: string;
  capex: string;
  payback: string;
  keyModels: string;
  priority: string;
}

export interface DashboardContent {
  kicker: string;
  title: string;
  lead: string;
  portfolioTitle: string;
  portfolioNote: string;
  calcTitle: string;
  calcLead: string;
  calcNote: string;
  packages: PackageSpec[];
}

export const dashboard = {
  fa: {
    kicker: 'داشبورد هیدروما',
    title: 'داشبورد علمی هیدروما نوژین',
    lead: 'داشبورد علمی هیدروما نوژین — مدل‌های علمی زنده برای آب، خاک، کشت و کربن.',
    portfolioTitle: 'پورتفولیوی ۱۲ بستهٔ فنی-مهندسی',
    portfolioNote: 'برآورد سرمایه‌گذاری و دورهٔ بازگشت سرمایه برای هر بستهٔ اجرایی.',
    calcTitle: 'محاسبه‌گرهای زندهٔ مدل‌ها',
    calcLead: 'پارامترها را تغییر دهید و نتیجه را بلافاصله ببینید؛ معادلات مطابق استانداردهای علمی (FAO، USDA، van Genuchten) پیاده‌سازی شده‌اند.',
    calcNote: 'خروجی هر محاسبه همراه روش، واحد و بازهٔ اعتبار نمایش داده می‌شود؛ برای تصمیم‌های اجرایی از داده‌های میدانی به‌روز استفاده کنید.',
    packages: [
      { code: 'HP-01', title: 'آبخوان زیستی', desc: 'شش لایهٔ خاک و مصالح بومی برای ذخیرهٔ عمیق بارش؛ نفوذ ۵×، تغذیهٔ آبخوان ۳×.', capex: '۳۰۰ $/هکتار', payback: '۱.۵ سال', keyModels: 'هورتون، SCS-CN، Van Genuchten، دارسی', priority: 'بحرانی' },
      { code: 'HP-02', title: 'کانال مارپیچ', desc: 'کانال مارپیچ ارشمیدسی برای افزایش زمان ماند آب ۴ برابری و بهبود ۸۰٪ کیفیت.', capex: '۳۵۰ $/هکتار', payback: '۲ سال', keyModels: 'مانینگ، رینولدز، فرود، سرریز فرانسیس', priority: 'بالا' },
      { code: 'HP-03', title: 'حلقهٔ سنگی', desc: '۲۵ حلقه در هکتار؛ ذخیرهٔ ۷۴۰ لیتر در هر حلقه، CN از ۸۰ به ۳۵.', capex: '۲۰۰ $/هکتار', payback: '۳–۴ سال', keyModels: 'ذخیرهٔ حلقه، هورتون، SCS-CN، پایداری', priority: 'بالا' },
      { code: 'HP-04', title: 'چالهٔ نفوذی', desc: 'سریع‌ترین بازگشت سرمایه (۲ سال)؛ نفوذ نقطه‌ای ارزان و مؤثر.', capex: '۷۵ $/هکتار', payback: '۲ سال', keyModels: 'هورتون، SCS-CN', priority: 'بحرانی' },
      { code: 'HP-05', title: 'بندک سنگی-آهکی', desc: 'بندک با عمر ۵۰+ سال؛ تثبیت آهکی و نگهداشت رسوب.', capex: '۴۵۰ $/هکتار', payback: '۳ سال', keyModels: 'هیدرولیک سرریز، پایداری', priority: 'بالا' },
      { code: 'HP-06', title: 'لایه‌بندی خاک', desc: 'بازسازی پروفیل خاک؛ AWC +۸۷٪، SOC +۸۸٪، فرسایش −۷۸٪.', capex: '۴۰۰ $/هکتار', payback: '۴ سال', keyModels: 'Van Genuchten، AWC، S-index، RUSLE', priority: 'بالا' },
      { code: 'HP-07', title: 'مالچ زیستی', desc: '۱۰۰٪ مواد طبیعی بومی؛ کاهش تبخیر و تثبیت رطوبت سطحی.', capex: '۱۵۰ $/هکتار', payback: '۲–۳ سال', keyModels: 'بیلان آب، رطوبت سطحی', priority: 'متوسط' },
      { code: 'HP-08', title: 'کشت چندلایه و آگروفارستری', desc: '۵ لایهٔ رویشی و ۲۵+ گونه؛ ترسیب کربن ۴۴ تن CO₂e در هکتار.', capex: '۹۵۰ $/هکتار', payback: '۵+ سال', keyModels: 'ترسیب کربن، RothC', priority: 'متوسط' },
      { code: 'HP-09', title: 'کنسرسیوم میکروبی', desc: '۱۲ سویهٔ مفید؛ تثبیت نیتروژن ۸۰–۲۲۰ کیلوگرم در هکتار در سال.', capex: '۱۲۰ $/هکتار', payback: '۲ سال', keyModels: 'چرخهٔ نیتروژن، زیست‌توده', priority: 'متوسط' },
      { code: 'HP-10', title: 'مدیریت آفات تلفیقی', desc: '۶ لایهٔ کنترل و ۱۸ عامل بیولوژیک؛ کاهش ۹۱٪ آفت‌کش شیمیایی.', capex: '۲۵۰ $/هکتار', payback: '۲–۳ سال', keyModels: 'پویایی آفت-شکارچی', priority: 'متوسط' },
      { code: 'HP-11', title: 'بادشکن زیستی', desc: '۳ ردیف گونه؛ کاهش ۶۰–۹۰٪ سرعت باد و ۹۶٪ فرسایش بادی.', capex: '۸۰۰ $/هکتار', payback: '۴–۵ سال', keyModels: 'سایهٔ باد، انتقال ذره', priority: 'متوسط' },
      { code: 'HP-12', title: 'پایش هوشمند و یکپارچه‌سازی', desc: 'مغز سیستم: ۶۱ سنسور در هکتار، ۱۲ مدل هوش مصنوعی، ۵۰ هزار داده در روز.', capex: '۵۰۰ $/هکتار', payback: 'ROI کل پورتفولیو ۱.۵×', keyModels: 'سری‌زمان، یادگیری ماشین', priority: 'یکپارچه‌ساز' },
    ],
  },
  en: {
    kicker: 'HyDroMa dashboard',
    title: 'The HyDroMa Nojin science dashboard',
    lead: '12 engineering restoration packages plus the live HyDroMa scientific models — water, soil, crops and carbon.',
    portfolioNote: 'Indicative investment and payback estimate for each implementation package.',
    portfolioTitle: 'The 12-package engineering portfolio',
    calcTitle: 'Live model calculators',
    calcLead: 'Adjust the parameters and see results instantly; the equations follow established scientific standards (FAO, USDA, van Genuchten).',
    calcNote: 'Every result shows its method, units and validity domain; use up-to-date field data for executive decisions.',
    packages: [
      { code: 'HP-01', title: 'Bio-Aquifer', desc: 'Six soil/material layers for deep rainfall storage; 5× infiltration, 3× aquifer recharge.', capex: '300 $/ha', payback: '1.5 years', keyModels: 'Horton, SCS-CN, Van Genuchten, Darcy', priority: 'Critical' },
      { code: 'HP-02', title: 'Spiral Channel', desc: 'Archimedean spiral channel; 4× hydraulic residence time and 80% water-quality improvement.', capex: '350 $/ha', payback: '2 years', keyModels: 'Manning, Reynolds, Froude, Francis weir', priority: 'High' },
      { code: 'HP-03', title: 'Stone Ring', desc: '25 rings per hectare; 740 L storage per ring, CN from 80 to 35.', capex: '200 $/ha', payback: '3–4 years', keyModels: 'Ring storage, Horton, SCS-CN, stability', priority: 'High' },
      { code: 'HP-04', title: 'Infiltration Pit', desc: 'Fastest payback (2 years); cheap and effective point infiltration.', capex: '75 $/ha', payback: '2 years', keyModels: 'Horton, SCS-CN', priority: 'Critical' },
      { code: 'HP-05', title: 'Stone-Lime Check Dam', desc: '50+ year lifespan; lime stabilization and sediment retention.', capex: '450 $/ha', payback: '3 years', keyModels: 'Weir hydraulics, stability', priority: 'High' },
      { code: 'HP-06', title: 'Soil Layering', desc: 'Soil profile reconstruction; AWC +87%, SOC +88%, erosion −78%.', capex: '400 $/ha', payback: '4 years', keyModels: 'Van Genuchten, AWC, S-index, RUSLE', priority: 'High' },
      { code: 'HP-07', title: 'Bio Mulch', desc: '100% natural local materials; reduced evaporation and surface moisture retention.', capex: '150 $/ha', payback: '2–3 years', keyModels: 'Water balance, surface moisture', priority: 'Medium' },
      { code: 'HP-08', title: 'Multi-Layer Agroforestry', desc: '5 growing layers and 25+ species; 44 t CO₂e carbon sequestration per hectare.', capex: '950 $/ha', payback: '5+ years', keyModels: 'Carbon sequestration, RothC', priority: 'Medium' },
      { code: 'HP-09', title: 'Microbial Consortium', desc: '12 beneficial strains; 80–220 kg/ha/yr nitrogen fixation.', capex: '120 $/ha', payback: '2 years', keyModels: 'Nitrogen cycle, biomass', priority: 'Medium' },
      { code: 'HP-10', title: 'Integrated Pest Management', desc: '6 control layers and 18 biological agents; 91% chemical pesticide reduction.', capex: '250 $/ha', payback: '2–3 years', keyModels: 'Pest-predator dynamics', priority: 'Medium' },
      { code: 'HP-11', title: 'Windbreak', desc: '3 species rows; 60–90% wind-speed and 96% wind-erosion reduction.', capex: '800 $/ha', payback: '4–5 years', keyModels: 'Wind shadow, particle transport', priority: 'Medium' },
      { code: 'HP-12', title: 'Smart Monitoring & Integration', desc: 'The system brain: 61 sensors/ha, 12 AI models, 50,000 data points/day.', capex: '500 $/ha', payback: 'Portfolio ROI 1.5×', keyModels: 'Time series, machine learning', priority: 'Integrator' },
    ],
  },
} satisfies Record<'fa' | 'en', DashboardContent>;

