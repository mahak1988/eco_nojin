/** Category page — shows all models in a category as cards
 * with short descriptions, bilingual. */

import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Search } from 'lucide-react';
import Seo from '../../components/ui/Seo';
import Reveal from '../../components/ui/Reveal';
import BaseCard, { type CardVariant } from '../../components/dashboard/BaseCard';
import { useLang } from '../../i18n/LanguageContext';
import { categories, registry, type RegistryEntry } from '../../lib/hydromaregistry';
import type { ModelImplementation } from '../../lib/hydromaregistry';

const VARIANT_MAP: Record<string, CardVariant> = {
  indices: 'leaf',
  formulas: 'aqua',
  soil: 'sand',
  hydro: 'aqua',
  simulation: 'leaf',
  carbon: 'sand',
  climate: 'aqua',
  economics: 'leaf',
};

const IMPL_LABEL: Record<string, { fa: string; en: string; className: string }> = {
  calculator: { fa: 'محاسبه‌گر زنده', en: 'Live calculator', className: 'bg-[var(--color-aqua-500)] text-[var(--color-aqua-300)]' },
  'engine+calculator': { fa: 'محاسبه‌گر + موتور', en: 'Calculator + engine', className: 'bg-[var(--color-leaf-500)] text-[var(--color-leaf-300)]' },
  'engine+api': { fa: 'سرویس محاسباتی', en: 'Computational service', className: 'bg-[var(--color-sand-500)] text-[var(--color-night-200)]' },
  engine: { fa: 'موتور محاسباتی', en: 'Computational engine', className: 'bg-[var(--color-sand-500)] text-[var(--color-night-200)]' },
};

function implBadge(impl: ModelImplementation, lang: 'fa' | 'en') {
  const label = IMPL_LABEL[impl];
  const text = lang === 'fa' ? label.fa : label.en;
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${label.className}`}>
      {text}
    </span>
  );
}

function ModelCard({ entry, variant }: { entry: RegistryEntry; variant: CardVariant }) {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  const name = isFa ? entry.nameFa : entry.nameEn;
  const desc = isFa ? entry.descFa : entry.descEn;

  return (
    <BaseCard variant={variant} title={name}>
      <p className="text-xs leading-6 text-[var(--color-night-200)]">{desc}</p>
      <div className="mt-2 flex items-center justify-between">
        {implBadge(entry.impl, lang)}
        <Link
          to={`/dashboard/models/${entry.id}`}
          className="rounded-full bg-[var(--color-night-900)] px-3 py-1 text-[11px] font-bold text-[var(--color-night-200)] hover:text-[var(--color-leaf-300)]"
        >
          {isFa ? 'مشاهده' : 'View'}
        </Link>
      </div>
    </BaseCard>
  );
}

export default function CategoryPage({ categoryKey }: { categoryKey: string }) {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const category = categories.find((c) => c.key === categoryKey);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'impl'>('name');

  const entries = useMemo(() => {
    let filtered = registry.filter((entry) => entry.category === categoryKey);
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (entry) =>
          entry.id.toLowerCase().includes(q) ||
          entry.nameFa.toLowerCase().includes(q) ||
          entry.nameEn.toLowerCase().includes(q) ||
          entry.descFa.toLowerCase().includes(q) ||
          entry.descEn.toLowerCase().includes(q)
      );
    }
    filtered.sort((a, b) => {
      if (sortBy === 'name') return (isFa ? a.nameFa : a.nameEn).localeCompare(isFa ? b.nameFa : b.nameEn);
      return a.impl.localeCompare(b.impl);
    });
    return filtered;
  }, [categoryKey, searchQuery, sortBy, isFa]);

  if (!category) {
    return (
      <div className="glass rounded-3xl p-8 text-center">
        <p className="text-sm text-[var(--color-night-200)]">{isFa ? 'دسته پیدا نشد.' : 'Category not found.'}</p>
        <Link to="/dashboard" className="mt-3 inline-block text-xs font-bold text-[var(--color-leaf-300)] hover:underline">
          {isFa ? 'بازگشت به داشبورد' : 'Back to dashboard'}
        </Link>
      </div>
    );
  }

  const title = isFa ? category.nameFa : category.nameEn;
  const variant = VARIANT_MAP[category.key] || 'night';

  return (
    <div className="flex flex-col gap-6">
      <Seo
        title={`${title} | ${t.brand.name}`}
        description={isFa ? category.nameFa : category.nameEn}
        path={`/dashboard/category/${category.key}`}
      />

      <Reveal className="flex flex-col gap-3">
        <Link
          to="/dashboard"
          className="inline-flex w-fit items-center gap-2 text-xs font-bold text-[var(--color-leaf-300)] hover:text-[var(--color-leaf-200)]"
        >
          <ArrowLeft className={`h-3.5 w-3.5 ${isFa ? '' : 'rotate-180'}`} aria-hidden />
          {isFa ? 'بازگشت به داشبورد' : 'Back to dashboard'}
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-3 py-1 text-[11px] font-extrabold bg-${variant}-500/15 text-${variant}-300`}>
            {entries.length} {isFa ? 'مدل' : 'models'}
          </span>
        </div>
        <h1 className="text-2xl font-extrabold leading-snug text-[var(--color-night-100)] sm:text-3xl">{title}</h1>
        <p className="max-w-3xl text-sm leading-8 text-[var(--color-night-200)]">
          {isFa
            ? `مجموعهٔ مدل‌های ${category.nameFa} — ${entries.length} مدل علمی`
            : `${category.nameEn} models — ${entries.length} scientific models`}
        </p>
      </Reveal>

      {/* Search and sort */}
      <Reveal>
        <div className="glass flex flex-col gap-3 rounded-2xl p-4 sm:flex-row sm:items-center sm:gap-4">
          <div className="flex flex-1 items-center gap-2 rounded-xl bg-[var(--color-night-900)] px-3 py-2">
            <Search className="h-4 w-4 text-[var(--color-night-200)]" aria-hidden />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={isFa ? 'جستجو در این دسته…' : 'Search in this category…'}
              className="w-full bg-transparent text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:outline-none"
              dir="ltr"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[11px] font-bold text-[var(--color-night-200)]">{isFa ? 'مرتب‌سازی:' : 'Sort:'}</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'impl')}
              className="rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] px-3 py-1.5 text-xs text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)] focus:outline-none"
            >
              <option value="name">{isFa ? 'نام' : 'Name'}</option>
              <option value="impl">{isFa ? 'نوع' : 'Type'}</option>
            </select>
          </div>
        </div>
      </Reveal>

      {/* Model cards grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {entries.map((entry, index) => (
          <Reveal key={entry.id} delay={(index % 3) * 0.05}>
            <ModelCard entry={entry} variant={variant} />
          </Reveal>
        ))}
      </div>

      {entries.length === 0 ? (
        <p className="text-center text-sm text-[var(--color-night-200)]">
          {isFa ? 'مدلی یافت نشد.' : 'No models found.'}
        </p>
      ) : null}
    </div>
  );
}
