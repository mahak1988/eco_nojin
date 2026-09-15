import { useState } from 'react';
import CounterWidget from '../sections/CounterWidget';
import { useLang } from '../../i18n/LanguageContext';

/** Carbon impact calculator. */
export default function ImpactCalculator() {
  const { lang } = useLang();
  const [trees, setTrees] = useState(100);
  const [years, setYears] = useState(5);

  const co2Saved = (trees * years * 22).toLocaleString();
  const areaRestored = (trees * 0.4).toLocaleString();

  return (
    <div className="rounded-3xl glass p-6 space-y-4">
      <h3 className="text-sm font-bold text-[var(--color-night-100)]">
        {lang === 'fa' ? 'محاسبه‌کر تأثیر' : 'Impact Calculator'}
      </h3>
      <div className="space-y-3">
        <div>
          <label className="text-xs text-[var(--color-night-200)]/60">
            {lang === 'fa' ? 'تعداد درختان' : 'Trees'}
          </label>
          <input
            type="range"
            min="10"
            max="1000"
            value={trees}
            onChange={(e) => setTrees(parseInt(e.target.value))}
            className="w-full mt-1 accent-[var(--color-leaf-500)]"
          />
        </div>
        <div>
          <label className="text-xs text-[var(--color-night-200)]/60">
            {lang === 'fa' ? 'سال‌های فعالیت' : 'Years'}
          </label>
          <input
            type="range"
            min="1"
            max="20"
            value={years}
            onChange={(e) => setYears(parseInt(e.target.value))}
            className="w-full mt-1 accent-[var(--color-leaf-500)]"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <CounterWidget value={parseInt(co2Saved)} label={lang === 'fa' ? 'kg CO₂ ذخیره' : 'CO₂ Saved'} suffix=" kg" />
        <CounterWidget value={parseInt(areaRestored)} label={lang === 'fa' ? 'هکتار بازیابی' : 'Ha Restored'} suffix=" ha" />
      </div>
    </div>
  );
}
