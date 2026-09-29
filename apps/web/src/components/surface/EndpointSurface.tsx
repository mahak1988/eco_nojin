import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { DataStateCard, SourceFooter, toDataState } from '@/app/[locale]/public/data-states';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';
import { ShapeView } from '@/components/surface/ShapeView';
import { Card } from '@/components/ui/Card';
import { type ApiResult } from '@/lib/api/client';
import { verificationOf } from '@/lib/api/surfaces';

/**
 * Shared shell for a catalogue surface whose contract declares no field.
 *
 * It renders exactly one honest state: the payload the gateway returned, the
 * offline or unavailable state when it did not answer, and an empty state when
 * the answer carried nothing. The page always names the exact path it read so a
 * reader can ask the gateway the same question.
 *
 * The provenance stamp is verified only when the payload itself claims
 * verification. A 200 proves the gateway answered, which is weaker than the
 * value having been measured — see `verificationOf`.
 */
export async function EndpointSurface({
  locale,
  source,
  title,
  description,
  result,
  emptyTitle,
  emptyDescription,
  count,
  backHref,
  children,
}: {
  locale: string;
  source: string;
  title: string;
  description: string;
  result: ApiResult<unknown>;
  emptyTitle: string;
  emptyDescription: string;
  count?: number;
  backHref?: string;
  children?: React.ReactNode;
}) {
  setRequestLocale(locale);
  const t = await getTranslations('surface');
  const state = toDataState(source, result, count ?? (result.ok ? 1 : 0));
  const verified = result.ok && verificationOf(result.data);

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-5xl px-6 pb-12 pt-8">
        <Link href={backHref ?? `/${locale}/system`} className="text-sm text-water hover:underline">
          {t('back')}
        </Link>

        <section className="mt-6">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="display text-3xl font-bold text-ink">{title}</h1>
            <ProvenanceStamp source={source} verified={verified} method={source} />
          </div>
          <p className="mt-3 max-w-3xl text-ink-soft">{description}</p>
          <p className="num mt-2 break-all text-xs text-ink-faint">{source}</p>
        </section>

        <section className="mt-6">
          <DataStateCard
            state={state}
            emptyTitle={emptyTitle}
            emptyDescription={emptyDescription}
          />
          {state.kind === 'ready' ? (
            <Card density="compact" className="mt-4">
              <p className="mb-3 text-xs text-ink-soft">{t('shapeNote')}</p>
              <p className="mb-3 text-xs text-ink-soft">
                {verified ? t('verifiedNote') : t('unverifiedNote')}
              </p>
              <ShapeView value={result.ok ? result.data : undefined} />
            </Card>
          ) : null}
          <SourceFooter state={state} />
        </section>

        {children}
      </div>
    </main>
  );
}
