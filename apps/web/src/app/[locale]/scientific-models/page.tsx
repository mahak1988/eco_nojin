import type { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { ListBlock } from '@/components/ListBlock';
import { SiteNav } from '@/components/SiteNav';
import { type DotState, StatusDot } from '@/components/StatusDot';
import { SITE_URL as BASE_URL } from '@/config/site';
import { apiGet, type CppStatus } from '@/lib/api/client';

const MODELS_PATH = '/api/v1/models';
const CARDS_PATH = '/api/v1/science/model-cards';
const CPP_PATH = '/api/v1/models/cpp-status';
const PINN_PATH = '/api/v1/models/pinn-status';
const ENGINE_PATH = '/api/v1/hydroma/models';

/** The engine inventory reports a validation block the shared type omits. */
type EngineModel = {
  id: string;
  name: string;
  category: string;
  description: string;
  version: string;
  language: string;
  reference?: string | null;
  status?: string | null;
  validation?: { status?: string | null; message?: string | null; last_validated?: string | null };
};

type ModelRegistry = {
  count: number;
  fidelity_counts: Record<string, number>;
  models: {
    slug: string;
    name_fa: string | null;
    name_en: string | null;
    domain: string;
    fidelity: string;
    reference: string | null;
    description: string | null;
    validity: string | null;
  }[];
};

type ModelCards = {
  count: number;
  cards: { slug: string; card: { validity?: string; limitations?: string } }[];
};

type PinnStatus = { available: boolean; note: string };

export const dynamic = 'force-dynamic';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('science');
  return {
    title: t('title'),
    description: t('lead'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/scientific-models`,
      title: t('title'),
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/scientific-models`,
      languages: {
        fa: `${BASE_URL}/fa/scientific-models`,
        en: `${BASE_URL}/en/scientific-models`,
      },
    },
  };
}

export default async function ScientificModelsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');
  const statusPage = await getTranslations('statusPage');
  const nf = new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en');

  const [registry, cards, cpp, pinn, engine] = await Promise.all([
    apiGet<ModelRegistry>(MODELS_PATH),
    apiGet<ModelCards>(CARDS_PATH),
    apiGet<CppStatus>(CPP_PATH),
    apiGet<PinnStatus>(PINN_PATH),
    apiGet<EngineModel[]>(ENGINE_PATH),
  ]);

  const endpoints = [registry, cards, cpp, pinn, engine];
  const reachable = endpoints.filter((result) => result.ok).length;
  const state: DotState = reachable === 0 ? 'down' : reachable === endpoints.length ? 'ok' : 'warn';

  const models = registry.ok ? registry.data.models : [];
  const limitations = new Map(
    (cards.ok ? cards.data.cards : []).map((entry) => [
      entry.slug,
      entry.card?.limitations ?? null,
    ]),
  );
  const engineRows = engine.ok ? engine.data : [];

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <div className="mx-auto max-w-4xl px-6 pb-12 pt-8">
        <h1 className="display text-balance text-4xl font-bold text-ink">{t('science.title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('science.lead')}</p>

        <section className="mt-8" aria-labelledby="model-sources">
          <h2 id="model-sources" className="field-label">
            {statusPage('endpoint')}
          </h2>
          <div className="mt-3 flex flex-wrap items-center gap-4">
            <StatusDot
              state={state}
              label={state === 'down' ? statusLine('unavailable') : statusLine('realData')}
            />
          </div>

          <ul className="mt-4 grid gap-3">
            <li className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">{MODELS_PATH}</span>
              <span className={registry.ok ? 'text-forest' : 'text-copper'}>
                {registry.ok ? nf.format(registry.data.count) : statusLine('unavailable')}
              </span>
            </li>
            <li className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">{CARDS_PATH}</span>
              <span className={cards.ok ? 'text-forest' : 'text-copper'}>
                {cards.ok ? nf.format(cards.data.count) : statusLine('unavailable')}
              </span>
            </li>
            <li className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">{CPP_PATH}</span>
              <span className={cpp.ok ? 'text-forest' : 'text-copper'}>
                {cpp.ok ? String(cpp.data.available) : statusLine('unavailable')}
              </span>
            </li>
            <li className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">{PINN_PATH}</span>
              <span className={pinn.ok ? 'text-forest' : 'text-copper'}>
                {pinn.ok ? String(pinn.data.available) : statusLine('unavailable')}
              </span>
            </li>
            <li className="card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <span className="font-mono text-xs text-ink">{ENGINE_PATH}</span>
              <span className={engine.ok ? 'text-forest' : 'text-copper'}>
                {engine.ok ? nf.format(engine.data.length) : statusLine('unavailable')}
              </span>
            </li>
          </ul>

          {registry.ok && (
            <ul className="mt-3 flex flex-wrap gap-2">
              {Object.entries(registry.data.fidelity_counts).map(([fidelity, value]) => (
                <li key={fidelity} className="chip num font-mono text-[11px]">
                  {fidelity}: {nf.format(value)}
                </li>
              ))}
            </ul>
          )}

          {cpp.ok && cpp.data.kernels.length > 0 && (
            <p className="mt-3 text-xs text-ink-soft">
              {t('science.kernels')}:{' '}
              <span className="font-mono">{cpp.data.kernels.join(' · ')}</span>
            </p>
          )}
        </section>

        {models.length > 0 && (
          <section className="mt-10" aria-labelledby="model-registry">
            <h2 id="model-registry" className="field-label">
              {t('science.modelsTitle')}
            </h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-ink-soft">
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('label')}</th>
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('service')}</th>
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('state')}</th>
                    <th className="py-2 text-start font-medium">{statusPage('result')}</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((model) => (
                    <tr key={model.slug} className="border-b border-line/50 align-top">
                      <td className="py-2 pe-4">
                        <span className="font-mono text-xs text-ink">{model.slug}</span>
                        <p className="mt-1 text-xs text-ink-soft">
                          {locale === 'fa'
                            ? (model.name_fa ?? model.name_en)
                            : (model.name_en ?? model.name_fa)}
                        </p>
                      </td>
                      <td className="py-2 pe-4 text-xs text-ink-soft">
                        {model.domain} · {model.fidelity}
                      </td>
                      <td className="py-2 pe-4 text-xs text-ink-soft">
                        {model.reference ?? statusLine('noData')}
                      </td>
                      <td className="py-2 text-xs text-ink-soft">
                        {limitations.get(model.slug) ?? model.validity ?? statusLine('noData')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {engineRows.length > 0 && (
          <section className="mt-10" aria-labelledby="engine-models">
            <h2 id="engine-models" className="field-label">
              {t('science.modelsPublicNote')}
            </h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-ink-soft">
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('label')}</th>
                    <th className="py-2 pe-4 text-start font-medium">{statusPage('service')}</th>
                    <th className="py-2 text-start font-medium">{statusPage('state')}</th>
                  </tr>
                </thead>
                <tbody>
                  {engineRows.map((model) => (
                    <tr key={model.id} className="border-b border-line/50 align-top">
                      <td className="py-2 pe-4">
                        <span className="font-mono text-xs text-ink">{model.id}</span>
                        <p className="mt-1 text-xs text-ink-soft">{model.name}</p>
                      </td>
                      <td className="py-2 pe-4 text-xs text-ink-soft">
                        {model.category} · {model.version} · {model.language}
                      </td>
                      <td className="py-2 text-xs text-ink-soft">
                        {model.validation?.status ?? model.status ?? statusLine('noData')}
                        {model.validation?.message ? ` · ${model.validation.message}` : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <div className="mt-6 grid gap-4">
          <ListBlock
            title={common('limitsLabel')}
            items={[t('science.cppMissing'), t('science.modelsPublicNote')]}
            tone="clay"
          />
          <ListBlock
            title={common('nextLabel')}
            items={[t('science.modelsEmpty'), t('science.modelsPublicNote')]}
            tone="moss"
          />
        </div>
      </div>
    </main>
  );
}
