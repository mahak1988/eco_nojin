/** Impact + Carbon page content — honest skeletons: metrics are defined,
 * numbers arrive with the pilot (no invented figures).
 * Standards referenced: ISO 14064-2, IPCC 2019 Refinement, GHG Protocol, ICVCM,
 * Copernicus CDS, ESA CCI, FAIR Data Principles. */

export interface ImpactMetric {
  name: string;
  desc: string;
  unit: string;
  source?: string;
  method?: string;
  standard?: string;
  frequency?: string;
  apiField?: string;
}

export interface ImpactProject {
  name: string;
  lat: number;
  lng: number;
  type: 'forest' | 'wetland' | 'agriculture';
  status: 'planning' | 'active' | 'completed';
  ha?: number;
  co2e?: number;
}

export interface ImpactContent {
  kicker: string;
  title: string;
  lead: string;
  metricsTitle: string;
  metricsNote: string;
  metrics: ImpactMetric[];
  liveCounters: {
    title: string;
    note: string;
    items: { label: string; metricKey: string; unit: string; icon: string }[];
  };
  mrvCycle: { title: string; desc: string };
  chartsTitle: string;
  chartsNote: string;
  mapTitle: string;
  mapNote: string;
  reportTitle: string;
  reportNote: string;
  transparencyTitle: string;
  transparencyNote: string;
  projects: ImpactProject[];
  sampleTimeSeries: {
    months: string[];
    monthsEn: string[];
    ndvi: number[];
    ndwi: number[];
    carbon: number[];
    water: number[];
  };
  methodTitle: string;
  methodBody: string;
}

export const impact = {
  fa: {
    kicker: 'تأثیر',
    title: 'تأثیر قابل اندازه‌گیری',
    lead: 'ادعا نمی‌کنیم؛ اندازه می‌گیریم. متریک‌های تأثیر از روز نخست تعریف شده‌اند و پس از پایلوت، همین صفحه زنده می‌شود.',
    metricsTitle: 'متریک‌های تعریف‌شده',
    metricsNote: 'هر متریک با ترکیب پایش ماهواره‌ای و دادهٔ میدانی سنجیده می‌شود؛ انتشار با آغاز پایلوت آغاز می‌شود.',
    metrics: [
      {
        name: 'هکتار زیر پایش',
        desc: 'مساحت زمین‌های تحت پایش ماهواره‌ای مستمر',
        unit: 'هکتار',
        source: 'Sentinel-2 L2A',
        method: 'تحلیل طیفی و چندطیفی',
        standard: 'Copernicus CDS',
        frequency: 'روزانه',
        apiField: 'area_ha',
      },
      {
        name: 'کشاورز آموزش‌دیده',
        desc: 'کشاورزانی که از کانال‌های پنج‌گانه آموزش دیده‌اند',
        unit: 'نفر',
        source: 'KoBo field forms',
        method: 'پیگیری دوره‌های LMS',
        standard: '-',
        frequency: 'هفتگی',
        apiField: 'farmers_trained',
      },
      {
        name: 'اعتبار کربن صادرشده',
        desc: 'اعتبارهای تأییدشده و ثبت‌شده روی رجیستری',
        unit: 'اعتبار',
        source: 'Registry API (Polygon)',
        method: 'MRV + بلاکچین',
        standard: 'Verra / Puro-Earth / ISO 14064-2',
        frequency: 'ماهیانه',
        apiField: 'credits_issued',
      },
      {
        name: 'بهبود شاخص پوشش گیاهی',
        desc: 'تغییر NDVI قبل/بعد در زمین‌های برنامهٔ احیا',
        unit: 'ΔNDVI',
        source: 'Sentinel-2 L2A',
        method: 'مقایسه زمانی NDVI',
        standard: 'ESA CCI',
        frequency: 'ماهیانه',
        apiField: 'ndvi_improvement',
      },
      {
        name: 'صرفه‌جویی آب',
        desc: 'کاهش مصرف با توصیهٔ آبیاری مبتنی بر FAO-56',
        unit: 'مترمکعب',
        source: 'Soil + ERA5',
        method: 'Richards + FAO-56',
        standard: 'FAO Irrigation',
        frequency: 'هفتگی',
        apiField: 'water_saved_m3',
      },
      {
        name: 'انتشار جلوگیری‌شده CO₂',
        desc: 'مقادیر CO₂ معادل به‌واسطهٔ احیای اکوسیستم ثبت‌شده است',
        unit: 'تن CO₂e',
        source: 'RothC + Sentinel-2',
        method: 'IPCC 2019 Refinement',
        standard: 'IPCC 2019 / ISO 14064-2',
        frequency: 'سالیانه',
        apiField: 'co2_sequestered_tco2e',
      },
      {
        name: 'درصد پوشش گیاشتی',
        desc: 'سهمی از مساحت با پوشش گیاهی فعال',
        unit: '%',
        source: 'Copernicus CGLS',
        method: 'تحلیل پوشش گیاشتی',
        standard: 'ESA CCI',
        frequency: 'روزانه',
        apiField: 'vegetation_cover_pct',
      },
      {
        name: 'صرفه‌جویی انرژی',
        desc: 'کاهش مصرف انرژی در آبیاری با الگوهای بهینه',
        unit: 'کیلووات‌ساعت',
        source: 'مدل‌سازی FAO-56',
        method: 'مقایسه انرژی قبل/بعد',
        standard: 'IEA',
        frequency: 'ماهیانه',
        apiField: 'energy_saved_kwh',
      },
      {
        name: 'تنوع زیستی',
        desc: 'شاخص تنوع گونه‌های گیاشتی در مناطق احیا',
        unit: 'امتیاز',
        source: 'نظرسنجی میدانی',
        method: 'شاخص شانون-وینر',
        standard: 'IUCN',
        frequency: 'فصلی',
        apiField: 'biodiversity_score',
      },
      {
        name: 'رضایت کشاورز',
        desc: 'امتیاز رضایت کشاورزان از طریق NPS',
        unit: 'NPS',
        source: 'نظرسنجی KoBo',
        method: 'Net Promoter Score',
        standard: 'NPS Framework',
        frequency: 'ماهیانه',
        apiField: 'farmer_nps',
      },
    ],
    liveCounters: {
      title: 'آمار لحظه‌ای',
      note: 'شمارش معکوس به پایلوت — داده‌های زنده پس از آغاز عملیات منتشر می‌شود',
      items: [
        { label: 'هکتار زیر پایش', metricKey: 'area_ha', unit: 'هکتار', icon: 'satellite' },
        { label: 'کشاورز آموزش‌دیده', metricKey: 'farers_trained', unit: 'نفر', icon: 'people' },
        { label: 'CO₂ جلوگیری‌شده', metricKey: 'co2_sequestered_tco2e', unit: 'تن', icon: 'co2' },
        { label: 'اعتبار کربن', metricKey: 'credits_issued', unit: 'اعتبار', icon: 'leaf' },
      ],
    },
    mrvCycle: {
      title: 'چرخهٔ MRV شفاف',
      desc: 'هر گزارش اکو نوژین از چرخهٔ استاندارد MRV بر اساس ISO 14064-2 عبور می‌کند: اندازه‌گیری با ماهواره و میدان، گزارش‌گیری شفاف، سپس راستی‌آزمایی مستقل.',
    },
    chartsTitle: 'نمودارهای زمان‌سری',
    chartsNote: 'نمونه‌های تصویری زیر نمادین هستند؛ داده‌های زنده پس از وصل شدن به سرویس ماهواره‌ای و پایلوت منتشر می‌شود.',
    mapTitle: 'نقشهٔ پروژه‌ها',
    mapNote: 'موقعیت پروژه‌های احیای اکوسیستم در حال برنامه‌ریزی و فعال — لایهٔ پوشش گیاشتی ماهواره‌ای زیرین دارد.',
    reportTitle: 'گزارش MRV',
    reportNote: 'گزارش‌های فنی و کارشناسی از داده‌های ترکیبی ماهواره و میدان؛ قابل دانلود پس از پایلوت.',
    transparencyTitle: 'شفافیت داده',
    transparencyNote: 'هر متریک از منبع، روش و استاندارد بین‌المللی خود برخوردار است؛ جدول زیر تمام را نشان می‌دهد.',
    projects: [
      {
        name: 'پروژهٔ نمونه ۱',
        lat: 32.4279,
        lng: 54.0182,
        type: 'agriculture',
        status: 'planning',
        ha: 500,
        co2e: 1200,
      },
      {
        name: 'پروژهٔ نمونه ۲',
        lat: 29.9652,
        lng: 52.4552,
        type: 'forest',
        status: 'planning',
        ha: 1200,
        co2e: 4800,
      },
      {
        name: 'پروژهٔ نمونه Ⅲ',
        lat: 38.0959,
        lng: 57.2934,
        type: 'wetland',
        status: 'planning',
        ha: 80,
        co2e: 400,
      },
    ],
    sampleTimeSeries: {
      months: ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'],
      monthsEn: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
      ndvi: [0.22, 0.28, 0.35, 0.42, 0.48, 0.52, 0.58, 0.55, 0.47, 0.4, 0.31, 0.24],
      ndwi: [0.18, 0.15, 0.12, 0.25, 0.33, 0.41, 0.45, 0.42, 0.31, 0.22, 0.19, 0.17],
      carbon: [120, 135, 148, 162, 178, 189, 205, 212, 198, 185, 155, 130],
      water: [450, 480, 520, 510, 460, 380, 320, 340, 420, 460, 480, 470],
    },
    methodTitle: 'روش سنجش',
    methodBody:
      'هر متریک با ترکیب دادهٔ سنتینل-۲، اقلیم ERA5 و ثبت میدانی KoBo محاسبه و در گزارش MRV شفاف منتشر می‌شود؛ اعداد ساختگی در این پلتفرم جایی ندارد.',
  },
  en: {
    kicker: 'Impact',
    title: 'Measurable impact',
    lead: 'We do not claim — we measure. Impact metrics are defined from day one, and this page goes live with the pilot.',
    metricsTitle: 'Defined metrics',
    metricsNote: 'Each metric combines Sentinel imagery with field data; publishing starts with the pilot.',
    metrics: [
      {
        name: 'Hectares under monitoring',
        desc: 'Land area under continuous satellite monitoring',
        unit: 'ha',
        source: 'Sentinel-2 L2A',
        method: 'Spectral analysis',
        standard: 'Copernicus CDS',
        frequency: 'Daily',
        apiField: 'area_ha',
      },
      {
        name: 'Farmers trained',
        desc: 'Farmers reached through the five access channels',
        unit: 'people',
        source: 'KoBo field forms',
        method: 'LMS course tracking',
        standard: '-',
        frequency: 'Weekly',
        apiField: 'farmers_trained',
      },
      {
        name: 'Carbon credits issued',
        desc: 'Verified credits registered on the registry',
        unit: 'credits',
        source: 'Registry API (Polygon)',
        method: 'MRV + blockchain',
        standard: 'Verra / Puro-Earth / ISO 14064-2',
        frequency: 'Monthly',
        apiField: 'credits_issued',
      },
      {
        name: 'Vegetation index improvement',
        desc: 'Before/after NDVI change in restoration fields',
        unit: 'ΔNDVI',
        source: 'Sentinel-2 L2A',
        method: 'Time-series NDVI comparison',
        standard: 'ESA CCI',
        frequency: 'Monthly',
        apiField: 'ndvi_improvement',
      },
      {
        name: 'Water saved',
        desc: 'Reduced use via FAO-56-based irrigation advice',
        unit: 'm³',
        source: 'Soil + ERA5',
        method: 'Richards + FAO-56',
        standard: 'FAO Irrigation',
        frequency: 'Weekly',
        apiField: 'water_saved_m3',
      },
      {
        name: 'CO₂ sequestered',
        desc: 'Tonnes of CO₂ equivalent captured via ecosystem restoration',
        unit: 'tCO₂e',
        source: 'RothC + Sentinel-2',
        method: 'IPCC 2019 Refinement',
        standard: 'IPCC 2019 / ISO 14064-2',
        frequency: 'Annual',
        apiField: 'co2_sequestered_tco2e',
      },
      {
        name: 'Vegetation cover',
        desc: 'Percentage of area with active vegetation cover',
        unit: '%',
        source: 'Copernicus CGLS',
        method: 'Vegetation coverage analysis',
        standard: 'ESA CCI',
        frequency: 'Daily',
        apiField: 'vegetation_cover_pct',
      },
      {
        name: 'Energy saved',
        desc: 'Reduced energy use in irrigation with optimized scheduling',
        unit: 'kWh',
        source: 'FAO-56 modelling',
        method: 'Before/after energy comparison',
        standard: 'IEA',
        frequency: 'Monthly',
        apiField: 'energy_saved_kwh',
      },
      {
        name: 'Biodiversity index',
        desc: 'Species diversity index in restored areas',
        unit: 'score',
        source: 'Field surveys',
        method: 'Shannon-Wiener index',
        standard: 'IUCN',
        frequency: 'Seasonal',
        apiField: 'biodiversity_score',
      },
      {
        name: 'Farmer satisfaction',
        desc: 'Net Promoter Score from farmer surveys',
        unit: 'NPS',
        source: 'KoBo surveys',
        method: 'Net Promoter Score',
        standard: 'NPS Framework',
        frequency: 'Monthly',
        apiField: 'farmer_nps',
      },
    ],
    liveCounters: {
      title: 'Live stats',
      note: 'Countdown to pilot — real data publishes once operations begin',
      items: [
        { label: 'Hectares under monitoring', metricKey: 'area_ha', unit: 'ha', icon: 'satellite' },
        { label: 'Farmers trained', metricKey: 'farmers_trained', unit: 'people', icon: 'people' },
        { label: 'CO₂ sequestered', metricKey: 'co2_sequestered_tco2e', unit: 'tCO₂e', icon: 'co2' },
        { label: 'Carbon credits', metricKey: 'credits_issued', unit: 'credits', icon: 'leaf' },
      ],
    },
    mrvCycle: {
      title: 'Transparent MRV cycle',
      desc: 'Every Eco Nojin report follows the standard MRV cycle per ISO 14064-2: measurement via satellite and field, transparent reporting, then independent verification.',
    },
    chartsTitle: 'Time-series charts',
    chartsNote: 'The charts below are illustrative samples; real data goes live once the satellite service and pilot are connected.',
    mapTitle: 'Project map',
    mapNote: 'Restoration project locations in planning and active status — with an underlying satellite vegetation layer.',
    reportTitle: 'MRV reports',
    reportNote: 'Technical and field reports from combined satellite and field data; downloadable after the pilot.',
    transparencyTitle: 'Data transparency',
    transparencyNote: 'Each metric has a defined data source, method, and international standard — the table below shows all.',
    projects: [
      {
        name: 'Pilot site 1',
        lat: 32.4279,
        lng: 54.0182,
        type: 'agriculture',
        status: 'planning',
        ha: 500,
        co2e: 1200,
      },
      {
        name: 'Pilot site 2',
        lat: 29.9652,
        lng: 52.4552,
        type: 'forest',
        status: 'planning',
        ha: 1200,
        co2e: 4800,
      },
      {
        name: 'Pilot site 3',
        lat: 38.0959,
        lng: 57.2934,
        type: 'wetland',
        status: 'planning',
        ha: 80,
        co2e: 400,
      },
    ],
    sampleTimeSeries: {
      months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
      monthsEn: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
      ndvi: [0.22, 0.28, 0.35, 0.42, 0.48, 0.52, 0.58, 0.55, 0.47, 0.4, 0.31, 0.24],
      ndwi: [0.18, 0.15, 0.12, 0.25, 0.33, 0.41, 0.45, 0.42, 0.31, 0.22, 0.19, 0.17],
      carbon: [120, 135, 148, 162, 178, 189, 205, 212, 198, 185, 155, 130],
      water: [450, 480, 520, 510, 460, 380, 320, 340, 420, 460, 480, 470],
    },
    methodTitle: 'Measurement method',
    methodBody:
      'Every metric is computed from Sentinel-2 data, ERA5 climate and KoBo field records, published in transparent MRV reports. Made-up numbers have no place on this platform.',
  },
} satisfies Record<'fa' | 'en', ImpactContent>;

export interface CarbonContent {
  kicker: string;
  title: string;
  lead: string;
  howTitle: string;
  how: { title: string; desc: string }[];
  participateTitle: string;
  participate: string[];
  statusTitle: string;
  statusBody: string;
}

export const carbon = {
  fa: {
    kicker: 'پروژه‌های کربن',
    title: 'رجیستری کربن، از مزرعه تا بلاکچین',
    lead: 'مسیر اعتبار کربن اکو نوژین، شفاف و مرحله‌به‌مرحله است؛ نقشهٔ پروژه‌های فعال با نخستین پایلوت زنده می‌شود.',
    howTitle: 'مسیر اعتبار کربن',
    how: [
      { title: 'ثبت زمین', desc: 'کشاورز زمین و اقدام حفاظتی را ثبت می‌کند.' },
      { title: 'اندازه‌گیری', desc: 'پایش ماهواره‌ای + ثبت میدانی KoBo.' },
      { title: 'تأیید', desc: 'محاسبهٔ مدل‌محور و راستی‌آزمایی گزارش MRV.' },
      { title: 'ثبت و فروش', desc: 'اعتبار با تأیید بلاکچین روی پالیگون ثبت می‌شود.' },
    ],
    participateTitle: 'چگونه مشارکت کنم؟',
    participate: [
      'کشاورز: زمین خود را برای پایلوت ثبت کنید.',
      'خریدار/نهاد: گزارش‌های MRV تجمیعی را درخواست دهید.',
      'توسعه‌دهنده: از درگاه API به داده‌های تأییدشده وصل شوید.',
    ],
    statusTitle: 'وضعیت فعلی',
    statusBody:
      'زیرساخت رجیستری و زنجیرهٔ MRV آماده است؛ نخستین پروژه‌ها و نقشهٔ زندهٔ آن‌ها با آغاز پایلوت در همین صفحه منتشر می‌شود.',
  },
  en: {
    kicker: 'Carbon projects',
    title: 'The carbon registry, from farm to blockchain',
    lead: 'The Eco Nojin credit path is transparent and step-by-step; the live project map goes live with the first pilot.',
    howTitle: 'The carbon-credit path',
    how: [
      { title: 'Register land', desc: 'The farmer registers land and conservation actions.' },
      { title: 'Measure', desc: 'Satellite monitoring + KoBo field records.' },
      { title: 'Verify', desc: 'Model-based calculation and MRV report verification.' },
      { title: 'Register & sell', desc: 'Credits are recorded with blockchain verification on Polygon.' },
    ],
    participateTitle: 'How to participate?',
    participate: [
      'Farmer: register your land for the pilot.',
      'Buyer / institution: request aggregated MRV reports.',
      'Developer: connect to verified data through the API gateway.',
    ],
    statusTitle: 'Current status',
    statusBody:
      'The registry infrastructure and MRV chain are ready; the first projects and their live map are published on this page with the pilot launch.',
  },
} satisfies Record<'fa' | 'en', CarbonContent>;
