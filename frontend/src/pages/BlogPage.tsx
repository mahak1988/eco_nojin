import { useMemo, useState } from 'react';
import { Info, Search } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';

/** Blog page — categories, client-side search, project notes. */
export default function BlogPage() {
  const { lang, t } = useLang();
  const categories = useMemo(
    () => ['All', ...Array.from(new Set(t.blog.posts.map((post) => post.category)))],
    [t],
  );
  const faLabel = lang === 'fa' ? 'همه' : 'All';
  const [category, setCategory] = useState(faLabel);
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return t.blog.posts.filter((post) => {
      const inCategory = category === faLabel || post.category === category;
      const matchesQuery =
        q === '' ||
        post.title.toLowerCase().includes(q) ||
        post.excerpt.toLowerCase().includes(q);
      return inCategory && matchesQuery;
    });
  }, [t, category, query, faLabel]);

  return (
    <>
      <Seo title={`${t.blog.title} | ${t.brand.name}`} description={t.blog.lead} path="/blog" />
      <PageHeader kicker={t.blog.kicker} title={t.blog.title} lead={t.blog.lead} />

      <section className="px-4 pb-6 sm:px-6">
        <Reveal className="mx-auto max-w-3xl">
          <div className="flex items-start gap-3 rounded-2xl border border-[var(--color-aqua-500)]/25 bg-[var(--color-aqua-500)]/8 p-4">
            <Info className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-aqua-300)]" aria-hidden />
            <p className="text-xs leading-6 text-[var(--color-aqua-200)]/90">{t.blog.note}</p>
          </div>
        </Reveal>
      </section>

      <section className="px-4 pb-6 sm:px-6">
        <div className="mx-auto flex max-w-3xl flex-col gap-4">
          <Reveal>
            <div className="glass flex items-center gap-3 rounded-2xl px-4 py-3">
              <Search className="h-4 w-4 shrink-0 text-[var(--color-leaf-300)]" aria-hidden />
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={lang === 'fa' ? 'جستجو در یادداشت‌ها…' : 'Search notes…'}
                className="w-full bg-transparent text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:outline-none"
                aria-label={lang === 'fa' ? 'جستجو در یادداشت‌ها' : 'Search notes'}
              />
            </div>
          </Reveal>
          <Reveal delay={0.05}>
            <div className="flex flex-wrap gap-2" role="group" aria-label={lang === 'fa' ? 'دسته‌بندی' : 'Categories'}>
              {categories.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setCategory(cat)}
                  aria-pressed={category === cat}
                  className={`rounded-full px-4 py-1.5 text-xs font-bold transition-colors ${
                    category === cat
                      ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]'
                      : 'glass text-[var(--color-night-200)]/70 hover:text-[var(--color-night-100)]'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      <section className="px-4 pb-6 sm:px-6">
        <div className="mx-auto flex max-w-3xl flex-col gap-6">
          {filtered.length === 0 ? (
            <p className="glass rounded-2xl p-6 text-center text-sm text-[var(--color-night-200)]/55">
              {lang === 'fa' ? 'یادداشتی مطابق جستجو پیدا نشد.' : 'No note matches your search.'}
            </p>
          ) : (
            filtered.map((post, index) => (
              <Reveal key={post.title} delay={index * 0.06}>
                <article className="glass glass-hover rounded-3xl p-7 sm:p-8">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="rounded-full bg-[var(--color-leaf-500)]/12 px-3 py-1 text-xs font-bold text-[var(--color-leaf-300)]">
                      {post.date}
                    </span>
                    <span className="rounded-full bg-[var(--color-aqua-500)]/12 px-3 py-1 text-xs font-bold text-[var(--color-aqua-300)]">
                      {post.category}
                    </span>
                    <h2 className="text-xl font-extrabold text-[var(--color-night-100)] sm:text-2xl">
                      {post.title}
                    </h2>
                  </div>
                  <p className="mt-3 text-sm font-bold leading-7 text-[var(--color-night-200)]/75">
                    {post.excerpt}
                  </p>
                  <div className="mt-4 flex flex-col gap-3 border-t border-white/8 pt-4">
                    {post.paragraphs.map((paragraph) => (
                      <p key={paragraph} className="text-sm leading-8 text-[var(--color-night-200)]/65">
                        {paragraph}
                      </p>
                    ))}
                    {post.sections?.map((section) => (
                      <div key={section.heading} className="flex flex-col gap-3 pt-2">
                        <h3 className="text-base font-extrabold text-[var(--color-leaf-300)]">{section.heading}</h3>
                        {section.paragraphs.map((paragraph) => (
                          <p key={paragraph} className="text-sm leading-8 text-[var(--color-night-200)]/65">
                            {paragraph}
                          </p>
                        ))}
                      </div>
                    ))}
                  </div>
                </article>
              </Reveal>
            ))
          )}
        </div>
      </section>

      <CtaBand />
    </>
  );
}
