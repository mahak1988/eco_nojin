import type { Metadata } from 'next';
import Link from 'next/link';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { AdminPageHeader } from '@/components/admin/AdminPageHeader';
import {
  AdminCapabilityTable,
  AdminSourceNote,
  AdminUnavailable,
} from '@/components/admin/AdminStates';
import { adminSectionHref, getAdminSection } from '@/components/admin/admin-sections';

// No queue contract exists, so this route renders its registered state only.
export const dynamic = 'force-dynamic';

const section = getAdminSection('jobs');
const NEXT_SECTIONS = ['system-health', 'feature-flags', 'security'] as const;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return {
    title: t('common.pending'),
    description: t('statusPage.subtitle'),
    robots: { index: false, follow: false },
  };
}

export default async function JobsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <div>
      <AdminPageHeader locale={locale} section={section} />

      <section className="mt-6" aria-labelledby="admin-jobs-state">
        <h2 id="admin-jobs-state" className="field-label">
          {t('statusPage.state')}
        </h2>
        <ul className="mt-3 space-y-4">
          {section.capabilities.map((capability) => (
            <li key={capability.id}>
              <AdminUnavailable
                source={capability.gap === '' ? capability.id : capability.gap}
                detail={t('market.template.unavailableDescription')}
              />
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-6 card p-5">
        <h2 className="field-label">{t('common.limits')}</h2>
        <p className="mt-2 text-sm text-ink-soft">{t('market.template.unavailableDescription')}</p>
        <p className="mt-3 text-sm text-ink-soft">{t('statusLine.noData')}</p>
      </section>

      <AdminCapabilityTable id="admin-jobs-contract" capabilities={section.capabilities} />

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

      <AdminSourceNote source="openapi.json" ok={false} />
    </div>
  );
}
