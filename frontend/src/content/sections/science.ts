import type { SiteContent } from './types';

export interface ScienceContent {
  fa: SiteContent['science'];
  en: SiteContent['science'];
}

export const science = {
  fa: {
    kicker: 'موتور علمی هیدروما',
    title: 'مدل‌های فیزیکی، نه حدس و گمان',
    lead: 'هیدروما مدل‌های قطعی علوم زمین را با دادهٔ ماهواره‌ای و لایهٔ اقتصاد ترکیب می‌کند تا خروجی، «درجهٔ تصمیم» داشته باشد.',
    steps: [
      {
        title: 'مشاهده',
        desc: 'دادهٔ سنتینل-۲، اقلیم ERA5 و خاک SoilGrids گردآوری می‌شود.',
      },
      {
        title: 'شبیه‌سازی',
        desc: 'مدل‌های فیزیکی قطعی هیدروما زمین، آب و کربن را پیش‌بینی می‌کنند.',
      },
      {
        title: 'بهینه‌سازی',
        desc: 'سناریوها مقایسه و با NSGA-II بهینه می‌شوند.',
      },
      {
        title: 'تصمیم و MRV',
        desc: 'گزارش شفاف و قابل اعتماد برای اقدام و ثبت کربن.',
      },
    ],
    modelsTitle: 'هستهٔ مدل‌ها',
    models: [
      { name: 'Richards', desc: 'جریان آب در خاک غیراشباع', detail: 'معادلهٔ ریچاردز-برینسلی حرکت آب در خاک غیراشباع؛ ورودی میله‌ای، خروجی عمق آب‌رسانی و زهکشی.', slug: 'richards' },
      { name: 'Saint-Venant', desc: 'هیدرولیک جریان سطحی', detail: 'معادلات کنترل جریان غیرپایدار؛ شبیه‌سازی سیلابی و جریان شیب‌دار در حوزه‌های آبخیز.', slug: 'saint-venant' },
      { name: 'FAO-56', desc: 'تبخیر-تعرق گیاه مرجع', detail: 'روش استاندارد FAO-56 برای محاسبهٔ تعریق ارجاع و آب مورد نیاز گیاه؛ مبنای توصیه آبیاری دقیق.', slug: 'fao-56' },
      { name: 'RUSLE', desc: 'تلفات خاک ناشی از فرسایش', detail: 'معادلهٔ عرضه‌کنندهٔ فرسایش (RUSLE) برای پیش‌بینی تلفات خاک بر حسب تن/هکتار/سال.', slug: 'rusle' },
      { name: 'SWAT', desc: 'شبیه‌سازی حوزهٔ آبخیز', detail: 'ماژول مقیاس‌پذیر حوزهٔ آبخیز برای شبیه‌سازی هیدرولوژی، آب‌رسانی و بارش در مقیاس بزرگ.', slug: 'swat' },
      { name: 'RothC', desc: 'چرخهٔ کربن آلی خاک', detail: 'مدل عددی تجزیه و انباشت کربن آلی خاک (RothC-26.3); خروجی CO₂ معادل ذخایر کربن خاک.', slug: 'rothc' },
      { name: 'AquaCrop', desc: 'بهره‌وری آب در عملکرد محصول', detail: 'ماژول FAO برای ارتباط بین آب مصرفی، عملکرد و بهره‌وری آب؛ بهینه‌سازی آبیاری کشاورزی.', slug: 'aquacrop' },
      { name: 'NSGA-II', desc: 'بهینه‌سازی چندهدفی سناریوها', detail: 'الگوریتم ژنتیکی بهینه‌سازی چندهدفی غیرخطی برای یافتن فراموشهای Pareto در سناریوهای مدیریتی.', slug: 'nsga-ii' },
      { name: 'HEC-RAS / Manning', desc: 'هیدرولیک جریان رودخانه', detail: 'ماژول عددی HEC-RAS برای شبیه‌سازی جریان رودخانه با معادلهٔ مانینگ؛ هشدار سیلاب.', slug: 'hec-ras' },
    ],
    outputsTitle: 'خروجی‌های تصمیم‌ساز',
    outputsLead:
      'نتیجهٔ زنجیرهٔ علمی، محصولات مشخصی است که مستقیم به تصمیم مزرعه و گزارش سازمانی وصل می‌شود.',
    outputs: [
      'نقشه‌های ریسک فرسایش و سناریوهای حفاظت خاک.',
      'توصیهٔ آبیاری مبتنی بر FAO-56 و دادهٔ اقلیمی واقعی.',
      'مقایسهٔ سناریوها با شاخص‌های اقتصادی.',
      'گزارش MRV قابل اعتماد برای اعتبار کربن.',
    ],
    dataSourcesTitle: 'منابع داده',
    dataSources: [
      { name: 'Sentinel-2 / 1', desc: 'تصاویر ماهواره‌ای کوپرنیکوس (CDSE)' },
      { name: 'ERA5', desc: 'بازتحلیل اقلیمی کوپرنیکوس' },
      { name: 'SoilGrids', desc: 'نقشهٔ جهانی ویژگی‌های خاک' },
      { name: 'C++ Core', desc: 'هستهٔ عددی سریع با pybind11' },
    ],
    more: 'آشنایی بیشتر با موتور علمی',
  },
  en: {
    kicker: 'The HyDroMa engine',
    title: 'Physics-based models, not guesswork',
    lead: 'HyDroMa combines deterministic earth-science models with satellite data and an economics layer, so every output is decision-grade.',
    steps: [
      {
        title: 'Observe',
        desc: 'Sentinel-2 imagery, ERA5 climate and SoilGrids soil data are collected.',
      },
      {
        title: 'Simulate',
        desc: 'Deterministic physical models project land, water and carbon.',
      },
      {
        title: 'Optimize',
        desc: 'Scenarios are compared and optimized with NSGA-II.',
      },
      {
        title: 'Decide & MRV',
        desc: 'Transparent, trustworthy reporting for action and carbon registration.',
      },
    ],
    modelsTitle: 'Core models',
    models: [
      { name: 'Richards', desc: 'Water flow in unsaturated soil', detail: 'The Richards-Brillianti equation governs water movement in unsaturated soil; computes infiltration depth and drainage from matric potential.', slug: 'richards' },
      { name: 'Saint-Venant', desc: 'Surface-flow hydraulics', detail: 'The Saint-Venant equations model unsteady open-channel flow; simulates flood extent and flow over sloping terrain in watersheds.', slug: 'saint-venant' },
      { name: 'FAO-56', desc: 'Reference-crop evapotranspiration', detail: 'The FAO-56 Penman-Monteith standard computes reference evapotranspiration; the basis for precision irrigation scheduling.', slug: 'fao-56' },
      { name: 'RUSLE', desc: 'Soil loss from erosion', detail: 'The Revised Universal Soil Loss Equation (RUSLE) predicts soil erosion in tonnes per hectare per year under given management.', slug: 'rusle' },
      { name: 'SWAT', desc: 'Watershed simulation', detail: 'A scalable watershed model for simulating hydrology, irrigation and precipitation at catchment scale.', slug: 'swat' },
      { name: 'RothC', desc: 'Soil organic carbon turnover', detail: 'The RothC-26.3 numerical model tracks decomposition and accumulation of soil organic carbon; yields CO₂-equivalent soil carbon stocks.', slug: 'rothc' },
      { name: 'AquaCrop', desc: 'Crop water productivity', detail: 'The FAO AquaCrop module links water use to yield and water productivity; used for irrigation optimisation.', slug: 'aquacrop' },
      { name: 'NSGA-II', desc: 'Multi-objective scenario optimization', detail: 'A genetic multi-objective optimiser for finding Pareto fronts in management scenarios with conflicting goals.', slug: 'nsga-ii' },
      { name: 'HEC-RAS / Manning', desc: 'River-flow hydraulics', detail: 'HEC-RAS numerical module solves the Manning equation for river flow; drives flood early-warning outputs.', slug: 'hec-ras' },
    ],
    outputsTitle: 'Decision-grade outputs',
    outputsLead:
      'The scientific chain produces concrete products that plug straight into farm decisions and institutional reporting.',
    outputs: [
      'Erosion-risk maps and soil-conservation scenarios.',
      'Irrigation advice based on FAO-56 and real climate data.',
      'Scenario comparison with economic indicators.',
      'Trustworthy MRV reports for carbon credits.',
    ],
    dataSourcesTitle: 'Data sources',
    dataSources: [
      { name: 'Sentinel-2 / 1', desc: 'Copernicus satellite imagery (CDSE)' },
      { name: 'ERA5', desc: 'Copernicus climate reanalysis' },
      { name: 'SoilGrids', desc: 'Global soil-property mapping' },
      { name: 'C++ Core', desc: 'Fast numerical core via pybind11' },
    ],
    more: 'Get to know the scientific engine',
  },
} as const;

export type ScienceLang = 'fa' | 'en';
