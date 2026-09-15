import { useLang } from '../../i18n/LanguageContext';
import { Sun, CloudRain, Snowflake } from 'lucide-react';
import Reveal from '../ui/Reveal';

/** Seasonal content banner based on current month. */
export default function SeasonalBanner() {
  const { lang } = useLang();
  const month = new Date().getMonth();

  const seasons = [
    { name: 'spring', icon: Sun, labelFA: 'بهار', labelEN: 'Spring', color: '#7ee2a8' },
    { name: 'summer', icon: Sun, labelFA: 'تابستان', labelEN: 'Summer', color: '#e6b96b' },
    { name: 'autumn', icon: CloudRain, labelFA: 'پاییز', labelEN: 'Autumn', color: '#d49b3f' },
    { name: 'winter', icon: Snowflake, labelFA: 'زمستان', labelEN: 'Winter', color: '#7fd8e8' },
  ];

  const seasonIndex = month < 3 ? 0 : month < 6 ? 1 : month < 9 ? 2 : 0;
  const season = seasons[seasonIndex];
  const Icon = season.icon;

  return (
    <Reveal>
      <section className="px-4 py-12 sm:px-6" aria-label="Seasonal content">
        <div
          className="mx-auto max-w-6xl rounded-3xl border p-6 flex items-center gap-4"
          style={{ borderColor: `${season.color}30`, background: `${season.color}10` }}
        >
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl" style={{ backgroundColor: `${season.color}20`, color: season.color }}>
            <Icon className="h-6 w-6" aria-hidden />
          </div>
          <div>
            <p className="text-xs font-bold" style={{ color: season.color }}>
              {lang === 'fa' ? 'فصل فعلی' : 'Current Season'}
            </p>
            <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">
              {lang === 'fa' ? `پروژه‌ها در فصل ${season.labelFA}` : `${season.labelEN} Projects`}
            </h2>
            <p className="text-sm text-[var(--color-night-200)]/60">
              {lang === 'fa'
                ? 'فعالیت‌های بذرکاری و احیای زمین در این فصل برتر هستند.'
                : 'Planting and land restoration activities peak in this season.'}
            </p>
          </div>
        </div>
      </section>
    </Reveal>
  );
}
