/** Shared data models for all HomePage features */

export interface MetricData {
  label: string;
  value: number;
  secondary?: number;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  secondary?: number;
  category?: string;
}

export interface Project {
  id: string;
  name: string;
  location: string;
  status: 'active' | 'planning' | 'completed';
  area: number;
  type: 'forest' | 'wetland' | 'agriculture';
  lat: number;
  lng: number;
  progress: number;
}

export interface Testimonial {
  name: string;
  role: string;
  text: string;
  avatar: string;
}

export interface NewsItem {
  title: string;
  date: string;
  excerpt: string;
  category: string;
}

export interface Milestone {
  date: string;
  title: string;
  description: string;
  achieved: boolean;
}

export const SAMPLE_PROJECTS: Project[] = [
  { id: '1', name: 'جنگلشکاری مشهد', location: 'مشهد', status: 'active', area: 2400, type: 'forest', lat: 36.3, lng: 59.6, progress: 72 },
  { id: '2', name: 'بازسازی تالاب انزلی', location: 'انزلی', status: 'active', area: 1800, type: 'wetland', lat: 37.4, lng: 49.9, progress: 58 },
  { id: '3', name: 'کشاورزی پایدار اصفهان', location: 'اصفهان', status: 'planning', area: 3200, type: 'agriculture', lat: 32.4, lng: 51.7, progress: 15 },
  { id: '4', name: 'جنگلداری تبریز', location: 'تبریز', status: 'completed', area: 1600, type: 'forest', lat: 38.0, lng: 46.3, progress: 100 },
  { id: '5', name: 'بوم‌بانی رشت', location: 'رشت', status: 'active', area: 2100, type: 'wetland', lat: 37.3, lng: 49.6, progress: 85 },
  { id: '6', name: 'باغ‌های یاسوج', location: 'یاسوج', status: 'planning', area: 900, type: 'forest', lat: 31.0, lng: 50.9, progress: 8 },
];

export const CHART_MONTHLY_DATA: ChartDataPoint[] = [
  { label: 'فروردین', value: 420, secondary: 380 },
  { label: 'اردیبهشت', value: 510, secondary: 450 },
  { label: 'خرداد', value: 380, secondary: 520 },
  { label: 'تیر', value: 620, secondary: 490 },
  { label: 'مرداد', value: 750, secondary: 610 },
  { label: 'شهریور', value: 590, secondary: 680 },
  { label: 'مهر', value: 810, secondary: 720 },
  { label: 'آبان', value: 950, secondary: 830 },
  { label: 'آذر', value: 720, secondary: 900 },
  { label: 'دی', value: 860, secondary: 780 },
  { label: 'بهمن', value: 1100, secondary: 950 },
  { label: 'اسفند', value: 980, secondary: 1100 },
];

export const TESTIMONIALS_DATA = [
  { name: 'دکتر سارا مهرپور', role: 'مدیر علمی', text: 'پلتفرم Eco Nojin دقت و سرعت بی‌سابقه‌ای در پایش مناطق روستایی داشته است.', avatar: '👩‍🔬' },
  { name: 'مهندس رضا کریمی', role: 'مدیر فنی', text: 'مدل‌سازی سه‌بعدی حجم آب و بازدهی کشاورزی فوق‌العاده دقیق است.', avatar: '👨‍💻' },
  { name: 'دکتر نیلوفر حسینی', role: 'محقق ارشد', text: 'توانمندسازی جامعه‌های محلی با ابزارهای دیجیتال، رؤیای ما بود.', avatar: '👩‍🌾' },
];

export const NEWS_DATA = [
  { title: 'ردیابی پروژه جنگلشکاری مشهد', date: '1۴۰۵/۰۶/۱۵', excerpt: 'پیشرفت ۷۲٪ در بازسازی جنگل‌های حاشیه شهری.', category: 'پروژه' },
  { title: 'روز جهانی آب', date: '۱۴۰۵/۰۵/۲۲', excerpt: 'شرکت در کنفرانس بین‌المللی مدیریت منابع آب.', category: 'رویداد' },
  { title: 'منتشر شدن مقاله تحقیقاتی', date: '۱۴۰۵/۰۴/۱۰', excerpt: 'استراتژی تغییر اقلیم در مناطق خشک.', category: 'تحقیق' },
];

export const MILESTONES_DATA = [
  { date: '۱۴۰۱/۰۱/۰۱', title: 'تأسیس پلتفرم', description: 'شروع فعالیت‌های دیجیتال', achieved: true },
  { date: '۱۴۰۲/۰۳/۱۵', title: 'اولین پروژه پایلوت', description: 'مشروع بازسازی جنگل', achieved: true },
  { date: '۱۴۰۳/۰۶/۲۰', title: 'مقیاس‌پذیری ملی', description: 'گسترش به ۱۴ استان', achieved: true },
  { date: '۱۴۰۴/۰۹/۱۰', title: 'مدل سه‌بعدی', description: 'راه‌اندازی مدل‌های سه‌بعدی', achieved: true },
  { date: '۱۴۰۵/۱۲/۰۱', title: 'هوش مصنوعی', description: 'پیش‌بینی با AI فعال‌سازی شد', achieved: false },
];
