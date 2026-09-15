import { useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { SAMPLE_PROJECTS } from '../../data/homeData';

/** Compare two projects side by side. */
export default function ComparisonTool() {
  const { lang } = useLang();
  const [selected, setSelected] = useState<[string, string]>(['1', '2']);
  const p1 = SAMPLE_PROJECTS.find((p) => p.id === selected[0]);
  const p2 = SAMPLE_PROJECTS.find((p) => p.id === selected[1]);

  if (!p1 || !p2) return null;

  const compare = (a: number, b: number) => {
    if (a > b) return `${a} > ${b}`;
    if (a < b) return `${a} < ${b}`;
    return `${a} = ${b}`;
  };

  return (
    <div className="rounded-3xl glass p-6">
      <h3 className="text-sm font-bold text-[var(--color-night-100)] mb-4">
        {lang === 'fa' ? 'مقایسه پروژه‌ها' : 'Compare Projects'}
      </h3>
      <div className="flex gap-2 mb-4">
        <select
          value={selected[0]}
          onChange={(e) => setSelected([e.target.value, selected[1]])}
          className="rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-xs text-[var(--color-night-100)]"
        >
          {SAMPLE_PROJECTS.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
        <span className="self-center text-[var(--color-night-200)]/40">vs</span>
        <select
          value={selected[1]}
          onChange={(e) => setSelected([selected[0], e.target.value])}
          className="rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-xs text-[var(--color-night-100)]"
        >
          {SAMPLE_PROJECTS.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>
      <div className="space-y-2 text-xs">
        <div className="flex justify-between p-2 rounded-lg bg-white/3">
          <span className="text-[var(--color-night-200)]/60">{lang === 'fa' ? 'مساحت' : 'Area'}</span>
          <span className="text-[var(--color-leaf-300)]">{compare(p1.area, p2.area)} ha</span>
        </div>
        <div className="flex justify-between p-2 rounded-lg bg-white/3">
          <span className="text-[var(--color-night-200)]/60">{lang === 'fa' ? 'پیشرفت' : 'Progress'}</span>
          <span className="text-[var(--color-leaf-300)]">{compare(p1.progress, p2.progress)}%</span>
        </div>
        <div className="flex justify-between p-2 rounded-lg bg-white/3">
          <span className="text-[var(--color-night-200)]/60">{lang === 'fa' ? 'نوع' : 'Type'}</span>
          <span className="text-[var(--color-leaf-300)]">{p1.type} vs {p2.type}</span>
        </div>
      </div>
    </div>
  );
}
