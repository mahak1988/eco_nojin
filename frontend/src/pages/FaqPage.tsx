import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';

/** FAQ page — client-side search + category filters + FAQPage JSON-LD. */
export default function FaqPage() {
  const { t, lang } = useLang();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<string>(t.faq.categories[0]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return t.faq.items.filter((item) => {
      const inCategory = category === t.faq.categories[0] || item.cat === category;
      const matchesQuery =
        q === '' || item.q.toLowerCase().includes(q) || item.a.toLowerCase().includes(q);
      return inCategory && matchesQuery;
    });
  }, [t, query, category]);

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: t.faq.items.map((item) => ({
      '@type': 'Question',
      name: item.q,
      acceptedAnswer: { '@type': 'Answer', text: item.a },
    })),
  };

  return (
    <>
      <Seo
        title={`${t.faq.title} | ${t.brand.name}`}
        description={t.faq.lead}
        path="/faq"
        jsonLd={jsonLd}
      />
      <PageHeader kicker={t.faq.kicker} title={t.faq.title} lead={t.faq.lead} />

      <section className="px-4 pb-10 sm:px-6">
        <div className="mx-auto flex max-w-3xl flex-col gap-5">
          {/* search */}
          <Reveal>
            <div className="glass flex items-center gap-3 rounded-2xl px-4 py-3">
              <Search className="h-4 w-4 shrink-0 text-leaf-300" aria-hidden />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={lang === 'fa' ? 'جستجو در پرسش‌ها…' : 'Search questions…'}
                className="w-full bg-transparent text-sm text-emerald-50 placeholder:text-emerald-100/30 focus:outline-none"
                aria-label={lang === 'fa' ? 'جستجو در پرسش‌ها' : 'Search questions'}
              />
            </div>
          </Reveal>

          {/* category chips */}
          <Reveal delay={0.05}>
            <div className="flex flex-wrap gap-2" role="group" aria-label={lang === 'fa' ? 'دسته‌بندی' : 'Categories'}>
              {t.faq.categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setCategory(cat)}
                  aria-pressed={category === cat}
                  className={`rounded-full px-4 py-1.5 text-xs font-bold transition-colors ${
                    category === cat
                      ? 'bg-leaf-500 text-night-950'
                      : 'glass text-emerald-100/70 hover:text-emerald-50'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </Reveal>

          {/* items */}
          {filtered.length === 0 ? (
            <p className="glass rounded-2xl p-6 text-center text-sm text-emerald-100/55">
              {lang === 'fa' ? 'موردی مطابق جستجو پیدا نشد.' : 'No question matches your search.'}
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              {filtered.map((item, index) => (
                <Reveal key={item.q} delay={Math.min(index * 0.03, 0.2)}>
                  <details className="glass group rounded-2xl open:border-leaf-500/30">
                    <summary className="flex cursor-pointer list-none items-center justify-between gap-3 p-5 text-sm font-extrabold text-emerald-50 marker:content-none hover:text-leaf-200 [&::-webkit-details-marker]:hidden">
                      <span>
                        <span className="me-2 rounded-full bg-aqua-500/12 px-2 py-0.5 text-[10px] font-bold text-aqua-300">
                          {item.cat}
                        </span>
                        {item.q}
                      </span>
                      <span
                        className="shrink-0 text-leaf-400 transition-transform group-open:rotate-45"
                        aria-hidden
                      >
                        +
                      </span>
                    </summary>
                    <p className="border-t border-white/8 px-5 py-4 text-sm leading-8 text-emerald-100/65">
                      {item.a}
                    </p>
                  </details>
                </Reveal>
              ))}
            </div>
          )}
        </div>
        <p className="mx-auto mt-8 max-w-3xl text-center text-xs text-emerald-100/40">
          {lang === 'fa'
            ? 'پرسش دیگری دارید؟ از صفحهٔ تماس بپرسید.'
            : 'Another question? Ask via the contact page.'}
        </p>
      </section>

      <CtaBand />
    </>
  );
}
