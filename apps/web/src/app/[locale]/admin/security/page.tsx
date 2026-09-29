import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import {
  AdminCapabilityTable,
  AdminRoleGate,
  AdminSourceNote,
  AdminUnavailable,
} from '@/components/admin/AdminStates';
import { adminSectionHref, getAdminSection } from '@/components/admin/admin-sections';
import { readAdminSession } from '@/components/admin/admin-server';
import { hasRole } from '@/lib/auth/roles';

// The audit contracts cannot answer truthfully, so nothing is listed here.
export const dynamic = 'force-dynamic';

const section = getAdminSection('security');
const NEXT_SECTIONS = ['users', 'system-health'] as const;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t('trust.title'),
    description: t('trust.lead'),
    robots: { index: false, follow: false },
  };
}

export default async function SecurityPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  const session = await readAdminSession();
  const sessionRole = session?.user.role ?? 'regular';
  const allowed = hasRole(sessionRole, section.roles);

  return (
    <div>
      <AdminPageHeader locale={locale} section={section} />

      <AdminRoleGate id="admin-security-roles" required={section.roles} sessionRole={sessionRole} />

      <section className="mt-6" aria-labelledby="admin-security-state">
        <h2 id="admin-security-state" className="field-label">
          {t('common.evidence')}
        </h2>
        <p className="mt-2 text-sm text-ink-soft">{t('trust.lead')}</p>
        <ul className="mt-4 space-y-4">
          {section.capabilities.map((capability) => (
            <li key={capability.id}>
              <AdminUnavailable
                source={capability.gap === '' ? capability.id : capability.gap}
                detail={t('market.template.unavailableDescription')}
                status={allowed ? 403 : 401}
              />
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-6 card p-5">
        <h2 className="field-label">{t('common.limits')}</h2>
        <p className="mt-2 text-sm text-ink-soft">{t('market.template.unavailableDescription')}</p>
        <p className="mt-3 text-sm text-ink-soft">{t('trust.what')}</p>
      </section>

      <AdminCapabilityTable id="admin-security-contract" capabilities={section.capabilities} />

      <section className="mt-6" aria-label={t('market.template.nextTitle')}>
        <h2 className="field-label">{t('market.template.nextTitle')}</h2>
        <p className="mt-2 text-sm text-ink-soft">{t('market.template.nextDescription')}</p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {NEXT_SECTIONS.map((id) => {
            const target = getAdminSection(id);
            return (
              <li key={id}>
                <Link
                  href={adminSectionHref(locale, target.path)}
                  className="chip hover:bg-[var(--surface-2)]"
                >
                  {t(target.labelKey)}
                </Link>
              </li>
            );
          })}
        </ul>
      </section>

      <AdminSourceNote source="services/api_gateway/routers/admin_security.py" ok={false} />
    </div>
  );
}
