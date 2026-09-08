import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { resources } from '../content/pages/marketreresources';

/** Resources page — knowledge hub categories with honest statuses. */
export default function ResourcesPage() {
  const { lang, t } = useLang();
  const c = resources[lang as 'fa' | 'en'];

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/resources" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="categories">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.categoriesTitle} />
          <div className="grid gap-4 sm:grid-cols-2">
            {c.categories.map((category, index) => (
              <Reveal key={category.title} delay={(index % 2) * 0.07}>
                <article className="glass glass-hover flex h-full flex-col gap-2 rounded-3xl p-6">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h3 className="text-base font-extrabold text-emerald-50">{category.title}</h3>
                    <span className="rounded-full border border-sand-500/30 bg-sand-500/10 px-3 py-1 text-[11px] font-bold text-sand-300">
                      {category.status}
                    </span>
                  </div>
                  <p className="text-sm leading-7 text-emerald-100/60">{category.desc}</p>
                </article>
              </Reveal>
            ))}
          </div>
          <Reveal>
            <div className="glass rounded-3xl p-7">
              <h2 className="text-base font-extrabold text-emerald-50">{c.contributeTitle}</h2>
              <p className="mt-2 text-sm leading-8 text-emerald-100/65">{c.contributeBody}</p>
            </div>
          </Reveal>
        </div>
      </section>

      <CtaBand />
    </>
  );
}
