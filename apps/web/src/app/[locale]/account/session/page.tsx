'use client';

import { useLocale } from 'next-intl';
import { useState } from 'react';
import { AuthErrorAlert } from '@/components/auth/AuthErrorAlert';
import type { AuthErrorKey } from '@/components/auth/errors';
import { errorDetail, toAuthErrorKey } from '@/components/auth/errors';
import { MachineTranslationNotice } from '@/components/auth/MachineTranslationNotice';
import { accountLanguageKey, roleLabelKey } from '@/components/auth/role-label';
import { useAuthMessage } from '@/components/auth/useAuthMessage';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { useAuth } from '@/components/providers/AuthProvider';
import { SiteNav } from '@/components/SiteNav';
import { Button } from '@/components/ui/Button';
import { Link } from '@/i18n/navigation';

export default function SessionPage() {
  const t = useAuthMessage();
  const locale = useLocale();
  const { user, loading, logout } = useAuth();
  const [signingOut, setSigningOut] = useState(false);
  const [failure, setFailure] = useState<{ messageKey: AuthErrorKey; detail?: string } | null>(
    null,
  );

  const roleKey = user ? roleLabelKey(user.role) : null;
  const languageKey = user ? accountLanguageKey(user.language) : null;
  const dateFormatter = new Intl.DateTimeFormat(locale, { dateStyle: 'long' });
  const memberSince = user ? formatDate(dateFormatter, user.created_at) : null;

  async function handleSignOut() {
    setSigningOut(true);
    setFailure(null);
    try {
      await logout();
    } catch (error) {
      setFailure({
        messageKey: toAuthErrorKey(error, 'auth.errors.signOutFailed'),
        detail: errorDetail(error),
      });
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto w-full max-w-2xl px-6 py-12">
        <h1 className="display text-3xl font-bold text-ink">{t('auth.session.title')}</h1>
        <p className="mt-3 text-sm text-ink-soft">{t('auth.session.lead')}</p>

        {loading ? (
          <p role="status" aria-busy="true" className="card mt-8 p-4 text-sm text-ink-soft">
            {t('auth.session.loading')}
          </p>
        ) : null}

        {!loading && !user ? (
          <div className="card mt-8 p-4">
            <p className="text-sm font-semibold text-ink">{t('auth.session.signedOut')}</p>
            <p className="mt-1 text-sm text-ink-soft">{t('auth.session.signedOutLead')}</p>
            <Link href="/auth/login" className="btn btn-primary mt-4 text-sm">
              {t('auth.common.signIn')}
            </Link>
          </div>
        ) : null}

        {!loading && user ? (
          <div className="card mt-8 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-sm font-semibold text-ink">{t('auth.session.signedIn')}</h2>
              <ProvenanceStamp
                source={t('auth.session.source')}
                method={t('auth.session.method')}
                verified={user.is_active && user.is_email_verified}
                labels={{
                  heading: t('auth.common.provenance.heading'),
                  source: t('auth.common.provenance.source'),
                  method: t('auth.common.provenance.method'),
                  verified: t('auth.common.provenance.verified'),
                  unverified: t('auth.common.provenance.unverified'),
                }}
              />
            </div>

            <dl className="mt-4 grid gap-3 sm:grid-cols-2">
              <SessionField label={t('auth.session.email')} value={user.email} dir="ltr" />
              <SessionField label={t('auth.session.fullName')} value={user.full_name} />
              <SessionField
                label={t('auth.session.role')}
                value={roleKey ? t(roleKey) : user.role}
              />
              <SessionField
                label={t('auth.session.language')}
                value={languageKey ? t(languageKey) : user.language}
              />
              <SessionField label={t('auth.session.country')} value={user.country} />
              <SessionField label={t('auth.session.city')} value={user.city} />
              <SessionField label={t('auth.session.phone')} value={user.phone} dir="ltr" />
              <SessionField label={t('auth.session.memberSince')} value={memberSince} />
            </dl>

            <ul className="mt-4 flex flex-wrap gap-3 text-xs">
              <li className="chip">
                {user.is_email_verified
                  ? t('auth.session.emailVerified')
                  : t('auth.session.emailNotVerified')}
              </li>
              <li className="chip">
                {user.is_active
                  ? t('auth.session.accountActive')
                  : t('auth.session.accountInactive')}
              </li>
            </ul>

            {failure ? (
              <div className="mt-4">
                <AuthErrorAlert messageKey={failure.messageKey} detail={failure.detail} />
              </div>
            ) : null}

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Button variant="danger" loading={signingOut} onClick={handleSignOut}>
                {signingOut ? t('auth.common.signingOut') : t('auth.common.signOut')}
              </Button>
              <Link href="/home" className="text-sm text-water hover:underline">
                {t('auth.common.backToHome')}
              </Link>
            </div>
          </div>
        ) : null}

        <MachineTranslationNotice className="mt-10" />
      </section>
    </main>
  );
}

function formatDate(formatter: Intl.DateTimeFormat, value: string | null | undefined) {
  if (typeof value !== 'string') return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : formatter.format(parsed);
}

function SessionField({
  label,
  value,
  dir,
}: {
  label: string;
  value: string | null | undefined;
  dir?: 'ltr';
}) {
  const t = useAuthMessage();

  return (
    <div>
      <dt className="text-xs text-ink-soft">{label}</dt>
      <dd className="text-sm text-ink" dir={dir}>
        {value || t('auth.session.unknown')}
      </dd>
    </div>
  );
}
