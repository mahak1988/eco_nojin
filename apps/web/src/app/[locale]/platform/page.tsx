import { getTranslations, setRequestLocale } from 'next-intl/server';
import { SiteNav } from '@/components/SiteNav';
import { Link } from '@/i18n/navigation';

export const dynamic = 'force-dynamic';

/** T03 — component gallery: four gateways into the live platform. */
export default async function PlatformPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const items = [
    {
      href: '/home' as const,
      title: t('platformOverview.itemHome'),
      desc: t('platformOverview.itemHomeDesc'),
    },
    {
      href: '/hydroma' as const,
      title: t('platformOverview.itemScience'),
      desc: t('platformOverview.itemScienceDesc'),
    },
    {
      href: '/market' as const,
      title: t('platformOverview.itemMarket'),
      desc: t('platformOverview.itemMarketDesc'),
    },
    {
      href: '/status' as const,
      title: t('platformOverview.itemStatus'),
      desc: t('platformOverview.itemStatusDesc'),
    },
  ];

  return (
    <main id="main">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="display text-balance text-4xl font-bold text-ink">
          {t('platformOverview.title')}
        </h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('platformOverview.lead')}</p>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {items.map((item, index) => (
            <article key={item.href} className="card flex flex-col gap-2 p-5">
              <span className="num text-xs text-ink-faint">{index + 1}</span>
              <h2 className="text-base font-semibold text-ink">{item.title}</h2>
              <p className="text-sm text-ink-soft">{item.desc}</p>
              <Link href={item.href} className="mt-2 text-sm text-water hover:underline">
                {t('platformOverview.cta')}
              </Link>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
