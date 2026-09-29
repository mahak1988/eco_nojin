import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';

import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { DemandForm } from './DemandForm';

export const dynamic = 'force-dynamic';

/** `POST /api/v1/marketplace/villages/b2b/demands`, declared in `village_hub.py`. */
const DEMANDS_SOURCE = '/api/v1/marketplace/villages/b2b/demands';
/** `GET /api/v1/marketplace/villages/b2b/demands/my` — the reader's own demands. */
const MY_DEMANDS_SOURCE = '/api/v1/marketplace/villages/b2b/demands/my';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.demand');
  return {
    title: t('title'),
    description: t('lead'),
    robots: { index: false, follow: true },
  };
}

/**
 * A page for a command is a form.
 *
 * `POST /marketplace/villages/b2b/demands` is the one marketplace mutation this
 * surface renders a form for. It is a good candidate and the other twenty-two
 * are not, and the difference is in the routers rather than in taste:
 *
 *   - the handler derives `buyer_id` from the session, so the form never asks a
 *     reader to name themselves, and `B2BDemandCreate.buyer_name` is optional so
 *     the form does not collect it either;
 *   - it moves no money, so it is clear of "escrow by default" and "a versioned
 *     contract before finance";
 *   - a read side exists — `GET /b2b/demands/my` — so a submitted demand can be
 *     shown to the reader afterwards.
 *
 * Every marketplace `POST` that moves money, settles, releases or cancels is
 * deliberately left without a page here; the catch-all names it, its read
 * contract and the absence of a form instead.
 */
export default async function B2BDemandPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('market.demand');

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-8">
        <header className="mb-8">
          <h1 className="display text-balance text-4xl font-bold text-ink">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('lead')}</p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <ProvenanceStamp source={DEMANDS_SOURCE} label={t('provenance')} method="POST" />
            <ProvenanceStamp source={MY_DEMANDS_SOURCE} label={t('listProvenance')} method="GET" />
          </div>
        </header>

        <DemandForm />

        <p className="mt-8 text-sm text-ink-soft">
          <Link
            href={`/${locale}/market/villages/b2b/demands/my`}
            className="text-forest underline"
          >
            {t('yourDemands')}
          </Link>
        </p>
      </div>
    </main>
  );
}
