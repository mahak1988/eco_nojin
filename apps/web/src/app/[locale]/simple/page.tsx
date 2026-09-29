import { getTranslations, setRequestLocale } from 'next-intl/server';
import { StatusDot } from '@/components/StatusDot';
import { apiGet } from '@/lib/api/client';
import { isUssdMenuLanguage } from '@/lib/domains/registry';

export const dynamic = 'force-dynamic';

type MenuPreview = { language: string; menu_text: string };
type GatewayStatus = { status: string; note?: string };

const MENU_PATH = '/api/v1/ussd/menu/preview';
const STATUS_PATH = '/api/v1/ussd/status';

/**
 * `/simple` — the low-bandwidth variant.
 *
 * "Lighter" is a claim about bytes, so it is enforced structurally rather than
 * asserted in a paragraph:
 *
 *   - no `next/image`, no `<img>`, no `SiteNav`, no `SiteFooter`. The chrome is
 *     the single largest thing on a public page and a reader on a weak network
 *     pays for every one of its links;
 *   - no client component and no `use client` island, so nothing here
 *     hydrates — the page is HTML and CSS the moment the response lands;
 *   - a document of a few hundred lines, with a plain vertical stack and no
 *     card grid, because layout cost is paid on every keystroke of scrolling on
 *     the handsets this page is for.
 *
 * The content is the same as the default variant: the gateway's own USSD menu
 * for the reader's language, the honest channel states, and the guarantee list
 * below, which is the page describing its own constraints.
 */
export default async function SimpleAccessPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('public.simple');
  const common = await getTranslations('common');
  const statusLine = await getTranslations('statusLine');

  const menuLanguage = isUssdMenuLanguage(locale) ? locale : null;
  const [menu, gateway] = await Promise.all([
    menuLanguage
      ? apiGet<MenuPreview>(`${MENU_PATH}?language=${menuLanguage}`)
      : Promise.resolve({ ok: false as const, status: 0, error: `language=${locale} not served` }),
    apiGet<GatewayStatus>(STATUS_PATH),
  ]);

  const guarantees = [
    t('guaranteeNoImages'),
    t('guaranteeNoScripts'),
    t('guaranteeSmall'),
    t('guaranteeLanguages'),
    t('guaranteeOffline'),
  ];

  return (
    <main id="main" className="mx-auto max-w-2xl px-4 py-6">
      <h1 className="display text-2xl font-bold text-ink">{t('metaTitle')}</h1>
      <p className="mt-2 text-sm text-ink-soft">{t('metaDescription')}</p>

      <h2 className="mt-6 text-base font-semibold text-ink">{t('guaranteeTitle')}</h2>
      <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-ink-soft">
        {guarantees.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <h2 className="mt-6 text-base font-semibold text-ink">{t('languagesTitle')}</h2>
      <p className="mt-1 text-sm text-ink-soft">{t('languagesBody')}</p>
      {menu.ok ? (
        <p className="num mt-2 text-sm whitespace-pre-wrap text-ink" dir="auto">
          {menu.data.menu_text}
        </p>
      ) : (
        <p className="mt-2 text-sm text-ink">{statusLine('unavailable')}</p>
      )}
      <p className="num mt-1 text-xs text-ink-faint">
        {menuLanguage
          ? `${MENU_PATH}?language=${menuLanguage}`
          : `${MENU_PATH}?language=${locale} · en, fa, ar`}
      </p>

      <h2 className="mt-6 text-base font-semibold text-ink">{common('error')}</h2>
      <ul className="mt-2 space-y-2 text-sm">
        <li className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-2">
          <span className="num font-mono text-xs text-ink">{STATUS_PATH}</span>
          <span className="flex items-center gap-2">
            <span className="num text-xs text-ink-soft">
              {gateway.ok ? gateway.data.status : statusLine('unavailable')}
            </span>
            <StatusDot
              state={gateway.ok ? 'ok' : 'down'}
              label={gateway.ok ? common('live') : statusLine('unavailable')}
            />
          </span>
        </li>
        <li className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-2">
          <span className="num font-mono text-xs text-ink">{MENU_PATH}</span>
          <span className="flex items-center gap-2">
            <span className="num text-xs text-ink-soft">
              {menu.ok ? statusLine('realData') : statusLine('unavailable')}
            </span>
            <StatusDot
              state={menu.ok ? 'ok' : 'down'}
              label={menu.ok ? common('live') : statusLine('unavailable')}
            />
          </span>
        </li>
      </ul>

      <p className="mt-6 text-xs text-ink-faint">{statusLine('realData')}</p>
    </main>
  );
}
