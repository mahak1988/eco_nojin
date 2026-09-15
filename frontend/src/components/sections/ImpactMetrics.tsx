import { useEffect, useState } from 'react';
import { Activity } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import ThreeDAreaChart from '../sections/ThreeDAreaChart';

interface DataPoint {
  label: string;
  value: number;
  secondary: number;
}

/** Live impact metrics with chart. */
export default function ImpactMetrics() {
  const { lang } = useLang();
  const [liveData, setLiveData] = useState<DataPoint[]>([]);

  useEffect(() => {
    const data: DataPoint[] = [
      { label: 'Jan', value: 0.4, secondary: 0.3 },
      { label: 'Feb', value: 0.5, secondary: 0.35 },
      { label: 'Mar', value: 0.6, secondary: 0.4 },
      { label: 'Apr', value: 0.7, secondary: 0.5 },
      { label: 'May', value: 0.8, secondary: 0.55 },
      { label: 'Jun', value: 0.9, secondary: 0.6 },
    ];
    setLiveData(data);
  }, []);

  return (
    <Reveal>
      <section className="px-4 py-16 sm:px-6 lg:py-24" id="impact-metrics" aria-labelledby="impact-heading">
        <div className="mx-auto max-w-6xl">
          <div className="mb-6 flex items-center gap-3">
            <Activity className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
            <p className="text-sm font-extrabold text-[var(--color-leaf-400)]">
              {lang === 'fa' ? 'تأثیر زنده' : 'Live Impact'}
            </p>
          </div>
          <h2 id="impact-heading" className="text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">
            {lang === 'fa' ? 'داشبورد تأثیر بلادرنگ' : 'Real-time Impact Dashboard'}
          </h2>

          <div className="mt-6 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
            <div className="rounded-3xl glass p-6">
              {liveData.length > 0 ? (
                <ThreeDAreaChart data={liveData.map((d) => ({ label: d.label, value: d.value }))} />
              ) : (
                <div className="h-[280px] flex items-center justify-center text-sm text-[var(--color-night-200)]/50">
                  {lang === 'fa' ? 'در حال بارگذاری...' : 'Loading...'}
                </div>
              )}
            </div>

            <div className="flex flex-col gap-3">
              {[
                { label: lang === 'fa' ? 'هکتار بازیابی' : 'Hectares Restored', value: '12,458' },
                { label: lang === 'fa' ? 'کاهش CO₂' : 'CO₂ Reduced', value: '3,201 t' },
                { label: lang === 'fa' ? 'پروژه فعال' : 'Active Projects', value: '47' },
                { label: lang === 'fa' ? 'کشاورزان تأثیرگیر' : 'Farmers Impacted', value: '8,930' },
              ].map((metric) => (
                <div key={metric.label} className="rounded-2xl glass p-4 flex items-center justify-between">
                  <span className="text-sm text-[var(--color-night-200)]/60">{metric.label}</span>
                  <span className="text-lg font-extrabold text-[var(--color-leaf-300)]">{metric.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </Reveal>
  );
}
