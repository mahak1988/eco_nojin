import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';

import { adminGet, adminToken, readAdminSession } from '@/components/admin/admin-server';
import { canonicalFor, languageAlternates } from '@/config/alternates';
import { SITE_URL as BASE_URL } from '@/config/site';

import { ledgerCopy } from '../../_lib/copy';
import {
  LedgerSurface,
  number,
  PlaceholderNotice,
  RecordList,
  record,
  resolveLedgerState,
  UnmeasuredCell,
} from '../../_lib/surface';

const SLUG = 'admin-admin-security-audit';
const ROUTE = '/admin/security/audit';
const PATH = '/api/v1/admin/security/audit';

/**
 * `GET /api/v1/admin/security/audit` —
 * `services/api_gateway/routers/admin_security.py:84`.
 *
 * `response_model=SecurityAuditResponse`, so the payload is one record.
 * `SecurityAuditResponse` is declared at `admin_security.py:69` with
 * `total_logins_24h`, `successful_logins`, `failed_logins`, `unique_users`,
 * `unique_ips`, `top_countries` and `suspicious_activities`.
 *
 * ## Two things this contract cannot answer
 *
 * First, it cannot answer at all today. `admin_security.py:54` does
 * `from database.models import LoginHistory`, and no `LoginHistory` class is
 * declared in `database/models.py` — the module defines `User`, `AuditLog`,
 * `ApiKey`, `ErrorLog` and seventy-odd others, and not that one. The import raises
 * when the dependency resolves, so this request returns a server error. That is
 * the console registry's recorded finding at `admin-sections.ts:304-319`, and the
 * page reports it as what it is: a failed request naming the contract.
 *
 * Second, even with the import fixed, two of the seven fields would still be
 * invented. `admin_security.py:105-112` returns a hard-coded `top_countries` list
 * and `admin_security.py:114-117` a hard-coded `suspicious_activities` list, each
 * marked "# (mock)". The five counts are real `func.count()` calls over the login
 * table, so the code below renders them and labels the other two as not measured.
 *
 * The window also does not mean what the field name says. `total_logins_24h` is
 * computed over the `hours` query parameter, which defaults to 24 and is not
 * fixed (`admin_security.py:87, 99`).
 */
interface Fetched {
  ok: boolean;
  status: number;
  data?: Record<string, unknown>;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  return {
    title: meta('title'),
    description: meta('description'),
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/admin/security`,
      title: meta('title'),
    },
    alternates: {
      canonical: canonicalFor(locale, '/admin/security'),
      languages: languageAlternates('/admin/security'),
    },
  };
}

export default async function Page({ params }: { params: Promise<{ locale: string }> }) {
  await params;
  const meta = await getTranslations(`pageMeta.${SLUG}`);
  const copy = await ledgerCopy('admin');

  const result: Fetched = await adminGet<Record<string, unknown>>(
    adminToken(await readAdminSession()),
    PATH,
  );
  const payload = record(result.ok ? result.data : undefined);
  const state = resolveLedgerState(result, result.ok ? 1 : 0);
  const c = copy.columns;
  const notMeasured = <UnmeasuredCell label={copy.notMeasured} />;

  return (
    <LedgerSurface
      catalogPath={ROUTE}
      namespace="admin"
      title={meta('title')}
      description={meta('description')}
      path={PATH}
      slug={SLUG}
      state={state}
      total={result.ok ? 1 : 0}
      ok={result.ok}
      stateDetail={result.ok ? undefined : `${PATH} · ${result.status}`}
      data={
        result.ok ? (
          <div className="flex flex-col gap-3">
            <PlaceholderNotice heading={copy.placeholderHeading} body={copy.placeholderBody} />
            <RecordList
              caption={meta('title')}
              fields={[
                { label: c.total, value: number(payload.total_logins_24h) },
                { label: c.status, value: number(payload.successful_logins) },
                { label: c.type, value: number(payload.failed_logins) },
                { label: c.member, value: number(payload.unique_users) },
                { label: c.source, value: number(payload.unique_ips) },
                { label: c.group, value: notMeasured },
                { label: c.action, value: notMeasured },
              ]}
            />
          </div>
        ) : null
      }
      detail={
        <p className="num text-xs text-ink-faint">
          {PATH} — services/api_gateway/routers/admin_security.py:105
        </p>
      }
    />
  );
}
