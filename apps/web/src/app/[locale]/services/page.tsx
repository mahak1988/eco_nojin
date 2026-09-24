import { getTranslations, setRequestLocale } from 'next-intl/server';
import { FivePart } from '@/components/FivePart';
import { SiteNav } from '@/components/SiteNav';

export const dynamic = 'force-dynamic';

export default async function ServicesPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const tracks = [
    { title: t('services.farmersTitle'), desc: t('services.farmersDesc') },
    { title: t('services.institutionsTitle'), desc: t('services.institutionsDesc') },
    { title: t('services.researchersTitle'), desc: t('services.researchersDesc') },
  ];

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <FivePart
          title={t('services.title')}
          lead={t('services.lead')}
          what={t('services.what')}
          audience={t('services.audience')}
          evidence={[
            t('services.farmersDesc'),
            t('services.institutionsDesc'),
            t('services.researchersDesc'),
          ]}
          limits={t.raw('services.limits') as string[]}
          next={t.raw('services.next') as string[]}
        />

        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          {tracks.map((track) => (
            <article key={track.title} className="card p-5">
              <h2 className="text-base font-semibold text-ink">{track.title}</h2>
              <p className="mt-2 text-sm text-ink-soft">{track.desc}</p>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
