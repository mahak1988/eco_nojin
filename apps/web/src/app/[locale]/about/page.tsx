import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { SiteNav } from '@/components/SiteNav';
import { SiteFooter } from '@/components/SiteFooter';
import { Link } from '@/i18n/navigation';

export const dynamic = 'force-dynamic';

export default async function AboutPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-5 py-10">
        <FivePart
          title={t('about.title')}
          lead={t('about.lead')}
          what={t('about.what')}
          audience={t('about.audience')}
          evidence={t.raw('about.evidence') as string[]}
          limits={t.raw('about.limits') as string[]}
          next={t.raw('about.next') as string[]}
        />

        <section className="panel mt-12 p-6" aria-labelledby="owner-heading">
          <h2 id="owner-heading" className="text-sm font-semibold text-[var(--ink-soft)]">
            {t('owner.sectionTitle')}
          </h2>
          <div className="mt-4 flex flex-wrap items-center gap-6">
            <img
              src="/brand/owner-narvan-logo-transparent.png"
              alt={t('owner.logoAlt')}
              className="h-20 w-auto"
            />
            <div className="max-w-md">
              <p className="text-sm font-semibold text-[var(--ink)]">{t('owner.role')}</p>
              <p className="mt-1 text-sm text-[var(--ink-soft)]">{t('owner.statement')}</p>
            </div>
          </div>
        </section>

        <nav className="mt-10 flex flex-wrap gap-3">
          <Link href="/statements" className="btn btn-ghost">
            {t('statements.title')}
          </Link>
          <Link href="/platform" className="btn btn-ghost">
            {t('platformOverview.title')}
          </Link>
          <Link href="/services" className="btn btn-ghost">
            {t('services.title')}
          </Link>
        </nav>
      </div>
      <SiteFooter />
    </main>
  );
}
