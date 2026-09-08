import { ArrowUpRight } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import { getApiBase } from '../lib/api';
import { useLang } from '../i18n/LanguageContext';
import { developers } from '../content/pages/developers';

/** Developers page — live Swagger link + auth/rate-limit facts + samples. */
export default function DevelopersPage() {
  const { lang, t } = useLang();
  const c = developers[lang as 'fa' | 'en'];
  const docsUrl = `${getApiBase()}/docs`;

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/developers" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 pb-8 sm:px-6">
        <Reveal className="mx-auto max-w-4xl">
          <div className="glass flex flex-col gap-3 rounded-3xl p-7 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col gap-1.5">
              <h2 className="text-base font-extrabold text-emerald-50">{c.docsTitle}</h2>
              <p className="text-sm leading-7 text-emerald-100/60">{c.docsBody}</p>
            </div>
            <a
              href={docsUrl}
              target="_blank"
              rel="noreferrer"
              dir="ltr"
              className="ring-glow inline-flex shrink-0 items-center gap-2 rounded-full bg-leaf-500 px-5 py-2.5 text-sm font-extrabold text-night-950 transition-transform hover:scale-[1.03]"
            >
              {c.docsButton}
              <ArrowUpRight className="h-4 w-4" aria-hidden />
            </a>
          </div>
        </Reveal>
      </section>

      <section className="px-4 pb-8 sm:px-6">
        <div className="mx-auto grid max-w-4xl gap-4 md:grid-cols-2">
          <Reveal>
            <div className="glass h-full rounded-3xl p-7">
              <h2 className="text-base font-extrabold text-emerald-50">{c.authTitle}</h2>
              <div className="mt-3 flex flex-col gap-2">
                {c.authBody.map((p) => (
                  <p key={p} className="text-sm leading-7 text-emerald-100/60">{p}</p>
                ))}
              </div>
            </div>
          </Reveal>
          <Reveal delay={0.08}>
            <div className="glass h-full rounded-3xl p-7">
              <h2 className="text-base font-extrabold text-emerald-50">{c.rateTitle}</h2>
              <p className="mt-3 text-sm leading-7 text-emerald-100/60">{c.rateBody}</p>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6">
        <div className="mx-auto flex max-w-4xl flex-col gap-5">
          <Reveal>
            <h2 className="text-base font-extrabold text-emerald-50">{c.samplesTitle}</h2>
          </Reveal>
          {c.samples.map((sample, index) => (
            <Reveal key={sample.label} delay={index * 0.06}>
              <div className="glass rounded-2xl p-5">
                <p className="mb-3 text-xs font-bold text-aqua-300">{sample.label}</p>
                <pre
                  dir="ltr"
                  className="overflow-x-auto rounded-xl bg-black/40 p-4 text-xs leading-6 text-emerald-100/85"
                >
                  <code>{sample.code}</code>
                </pre>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <CtaBand />
    </>
  );
}
