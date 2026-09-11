import type { SiteContent } from './types';

export interface PlatformContent {
  fa: SiteContent['platform'];
  en: SiteContent['platform'];
}

export const platform = {
  fa: {
    kicker: 'پلتفرم',
    title: 'ماژول‌های اکو نوژین',
    lead: 'درگاه یکپارچهٔ API تمام ماژول‌ها را زیر یک سقف جمع می‌کند؛ از پروفایل خاک تا آموزش کشاورز.',
    modules: [
      {
        icon: 'soil',
        title: 'خاک و آب',
        desc: 'پروفایل خاک، نسبت کربن به نیتروژن و داده‌های میدانی.',
      },
      {
        icon: 'satellite',
        title: 'پایش ماهواره‌ای',
        desc: 'شاخص‌های پوشش گیاهی و سری‌های زمانی از سنتینل.',
      },
      {
        icon: 'climate',
        title: 'اقلیم و سناریو',
        desc: 'دادهٔ ERA5 و سناریوهای اقلیمی SSP برای برنامه‌ریزی.',
      },
      {
        icon: 'store',
        title: 'بازارگاه',
        desc: 'قیمت‌ها و عرضهٔ محلی برای پیوند تولید به بازار.',
      },
      {
        icon: 'coins',
        title: 'اکوکیف و پاداش',
        desc: 'مشوق‌های مالی برای رفتارهای حفاظتی.',
      },
      { icon: 'book', title: 'آموزش', desc: 'دوره‌های کشاورز (LMS) به زبان محلی.' },
      {
        icon: 'clipboard',
        title: 'پایش میدانی',
        desc: 'فرم‌های کوبو (KoBo) و دادهٔ دستی میدان.',
      },
      {
        icon: 'sync',
        title: 'همگام‌سازی آفلاین',
        desc: 'پایگاه محلی و صف همگام‌سازی برای اینترنت ضعیف.',
      },
    ],
    useCases: [
      { problem: 'پایین بودن بازده نسبت به کود', module: 'خاک و آب', output: 'توصیهٔ دقیق کود بر اساس نسبت C/N' },
      { problem: 'برداشت ناشیانه در برابر طغیان', module: 'اقلیم و سناریو', output: 'هشدار اقلیمی ۷ روزه برای برنامه‌ریزی برداشت' },
      { problem: 'قیمت فروش ناشفاف', module: 'بازارگاه', output: 'قیمت لحظه‌ای و پیش‌بینی ۱۴ روزهٔ محصول' },
    ],
    stack: {
      title: 'معماری، زیر یک سقف',
      lead: 'از مرورگر کاربر تا هستهٔ عددی C++؛ هر لایه یک مسئولیت روشن دارد.',
      layers: [
        { icon: 'globe', title: 'وب و PWA', desc: 'رابط کاربری React/TypeScript با پشتیبانی آفلاین.' },
        { icon: 'route', title: 'درگاه API', desc: 'FastAPI با احراز هویت JWT و محدودسازی نرخ.' },
        { icon: 'blocks', title: '۳۸ میکروسرویس', desc: 'از احراز هویت تا بازارگاه و گزارش‌گیری.' },
        { icon: 'flask', title: 'موتور هیدروما', desc: 'پایتون + هستهٔ عددی C++20 با pybind11.' },
        { icon: 'database', title: 'داده و نگهداشت', desc: 'Supabase روی PostgreSQL با سیاست‌های RLS.' },
        { icon: 'satellite', title: 'منابع بیرونی', desc: 'Sentinel-2/1، ERA5 و SoilGrids.' },
      ],
    },
    useCasesTitle: 'از مشکل به راه‌حل',
    useCasesLead: 'هرچه کشاورز با آن روبرو است، ماژول مناسب اکو نوژین خروجی متفاوتی می‌دهد.',
    useCasesProblem: 'مشکل کشاورز',
    useCasesModule: 'ماژول اکو نوژین',
    useCasesOutput: 'خروجی',
    apiDesc:
      'همهٔ سرویس‌ها از طریق درگاه FastAPI با مسیر /api/v1 در دسترس‌اند؛ با احراز هویت JWT، محدودسازی نرخ و مستندات تعاملی.',
  },
  en: {
    kicker: 'Platform',
    title: 'Eco Nojin modules',
    lead: 'A unified API gateway brings every module under one roof — from soil profiles to farmer education.',
    modules: [
      {
        icon: 'soil',
        title: 'Soil & water',
        desc: 'Soil profiles, C/N ratios and field data.',
      },
      {
        icon: 'satellite',
        title: 'Satellite monitoring',
        desc: 'Vegetation indices and time series from Sentinel.',
      },
      {
        icon: 'climate',
        title: 'Climate & scenarios',
        desc: 'ERA5 data and SSP climate scenarios for planning.',
      },
      {
        icon: 'store',
        title: 'Marketplace',
        desc: 'Local prices and supply, linking producers to markets.',
      },
      {
        icon: 'coins',
        title: 'EcoWallet & rewards',
        desc: 'Financial incentives for conservation behaviors.',
      },
      { icon: 'book', title: 'Education', desc: 'Farmer courses (LMS) in local languages.' },
      {
        icon: 'clipboard',
        title: 'Field monitoring',
        desc: 'KoBo forms and manual field data.',
      },
      {
        icon: 'sync',
        title: 'Offline sync',
        desc: 'Local database and sync queue for weak connectivity.',
      },
    ],
    useCases: [
      { problem: 'Low nutrient use efficiency', module: 'Soil & water', output: 'Precision fertilizer advice based on C/N ratio' },
      { problem: 'Blind harvest vs. flood risk', module: 'Climate & scenarios', output: '7-day extreme-weather alert for harvest planning' },
      { problem: 'Unclear produce price', module: 'Marketplace', output: 'Live price and 14-day forecast for the crop' },
    ],
    stack: {
      title: 'Architecture under one roof',
      lead: 'From the user’s browser to the C++ numerical core; every layer has one clear responsibility.',
      layers: [
        { icon: 'globe', title: 'Web & PWA', desc: 'React/TypeScript UI with offline support.' },
        { icon: 'route', title: 'API gateway', desc: 'FastAPI with JWT auth and rate limiting.' },
        { icon: 'blocks', title: '38 microservices', desc: 'From authentication to marketplace and reporting.' },
        { icon: 'flask', title: 'HyDroMa engine', desc: 'Python + C++20 numerical core via pybind11.' },
        { icon: 'database', title: 'Data & storage', desc: 'Supabase on PostgreSQL with RLS policies.' },
        { icon: 'satellite', title: 'External sources', desc: 'Sentinel-2/1, ERA5 and SoilGrids.' },
      ],
    },
    useCasesTitle: 'From problem to solution',
    useCasesLead: 'Whatever a farmer faces, an Eco Nojin module delivers a different output.',
    useCasesProblem: 'Farmer problem',
    useCasesModule: 'Eco Nojin module',
    useCasesOutput: 'Output',
    apiDesc:
      'All services are reachable through the FastAPI gateway at /api/v1, with JWT authentication, rate limiting and interactive docs.',
  },
} as const;

export type PlatformLang = 'fa' | 'en';
