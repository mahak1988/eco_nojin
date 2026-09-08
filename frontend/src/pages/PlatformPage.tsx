import { Server } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import ModulesGrid from '../components/sections/ModulesGrid';
import StackDiagram from '../components/sections/StackDiagram';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';

/** Platform page: module map, layered architecture and unified API gateway note. */
export default function PlatformPage() {
  const { t } = useLang();

  return (
    <>
      <Seo
        title={`${t.platform.title} | ${t.brand.name}`}
        description={t.platform.lead}
        path="/platform"
      />
      <PageHeader
        kicker={t.platform.kicker}
        title={t.platform.title}
        lead={t.platform.lead}
      />
      <ModulesGrid />
      <StackDiagram />

      <section className="px-4 pb-6 sm:px-6">
        <Reveal className="mx-auto max-w-6xl">
          <div className="glass flex flex-col gap-4 rounded-3xl p-8 sm:flex-row sm:items-center sm:gap-6">
            <span className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-aqua-500/12 text-aqua-300">
              <Server className="h-6 w-6" aria-hidden />
            </span>
            <div className="flex flex-col gap-1.5">
              <h3 className="text-base font-extrabold text-emerald-50">{t.platform.apiTitle}</h3>
              <p className="text-sm leading-7 text-emerald-100/60">{t.platform.apiDesc}</p>
            </div>
          </div>
        </Reveal>
      </section>

      <CtaBand />
    </>
  );
}
