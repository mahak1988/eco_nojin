import { getTranslations, setRequestLocale } from 'next-intl/server';
import { SiteNav } from '@/components/SiteNav';

export const dynamic = 'force-dynamic';

export default async function LegalPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const docs = [
    { title: t('legal.termsTitle'), body: t('legal.termsBody') },
    { title: t('legal.privacyTitle'), body: t('legal.privacyBody') },
    { title: t('legal.cookiesTitle'), body: t('legal.cookiesBody') },
  ];

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <article className="mx-auto max-w-3xl px-6 py-10">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="display text-4xl font-bold text-ink">{t('legal.title')}</h1>
          <span className="chip num">{t('legal.version')}</span>
        </header>
        <p className="mt-3 text-ink-soft">{t('legal.lead')}</p>

        {docs.map((doc) => (
          <section key={doc.title} className="card mt-6 p-6">
            <h2 className="field-label">{doc.title}</h2>
            <p className="mt-3 text-sm text-ink">{doc.body}</p>
          </section>
        ))}
      </article>
    </main>
  );
}
