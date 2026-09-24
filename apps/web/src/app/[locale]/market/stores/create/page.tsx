'use client';

import { useParams, useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';
import { FivePart } from '@/components/FivePart';

export default function StoreCreatePage() {
  const params = useParams();
  const { locale } = params;
  const searchParams = useSearchParams();
  const bazaar = searchParams.get('bazaar');
  const t = useTranslations('market.storeCreate');

  const mockBazaars = [
    { id: 'b001', name: 'بازارچه نهادی مرکزی', stores: 42, region: 'خراسان' },
    { id: 'b002', name: 'بازارچه روستایی شمالی', stores: 18, region: 'مازندران' },
    { id: 'b003', name: 'بازارچه تخصصی زعفران', stores: 12, region: 'کرمان' },
  ];

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-5xl px-6 pb-12 pt-6">
        <header className="mb-8">
          <nav className="mb-4">
            <a
              href={`/${locale}/market/stores`}
              className="text-sm text-ink-soft hover:text-ink underline"
            >
              ← {locale === 'fa' ? 'فروشگاه‌ها' : 'Stores'}
            </a>
          </nav>
          <ProvenanceStamp source="store-create" label="ایجاد فروشگاه — ۸ گام">
            <h1 className="display text-3xl font-bold text-ink sm:text-4xl">
              {t('title')}
            </h1>
          </ProvenanceStamp>
        </header>

        <Card className="mb-6">
          <p className="text-ink-soft">{t('description')}</p>
        </Card>

        <FivePart
          title={t('whyCreateStore')}
          lead={t('lead')}
          what={t('what')}
          audience={t('audience')}
          evidence={[
            '§5.2 — 38 stores per regional plan',
            '§6.1 — 5-part store creation template',
            '§7 — 8-step creation wizard',
          ]}
          limits={[
            'Scaffold: no live data until Phase 3 backend',
            'Bazaar selection: mandatory parent bazaar',
            'Compliance: PQ signatures not enforced until Phase 3',
          ]}
          next={[
            'Phase 3: API endpoints for store CRUD',
            'Phase 3: Inventory & order management',
            'Phase 3: Multi-vendor settlement',
          ]}
          evidenceLabel={locale === 'fa' ? 'پایه‌ها' : 'Evidence'}
          limitsLabel={locale === 'fa' ? 'محدودیت‌ها' : 'Limits'}
          nextLabel={locale === 'fa' ? 'گام بعدی' : 'Next'}
        />

        <section className="mx-auto max-w-5xl px-6 py-6">
          <h2 className="text-xl font-bold text-ink mb-4">{t('selectBazaar')}</h2>
          <p className="text-ink-soft mb-6">{t('selectBazaarDesc')}</p>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {mockBazaars.map(b => (
              <Card key={b.id} className="p-4 hover:border-primary transition-colors cursor-pointer">
                <h3 className="font-medium text-ink">{b.name}</h3>
                <p className="text-sm text-ink-soft">{b.region} — {b.stores} {t('stores')}</p>
                <div className="mt-3">
                  <Link href={`/${locale}/market/stores/create/step1?bazaar=${b.id}`}>
                    <Button className="w-full">{t('selectBazaarBtn')}</Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>

          {bazaar && (
            <Card className="mt-6 p-4 border-primary/30 bg-primary/5">
              <p className="text-sm text-primary">
                <strong>{t('preselected')}: </strong>
                {mockBazaars.find(b => b.id === bazaar)?.name}
                <Link href={`/${locale}/market/stores/create/step1?bazaar=${bazaar}`} className="ml-3 underline">
                  {t('continue')}
                </Link>
              </p>
            </Card>
          )}
        </section>
      </div>
    </main>
  );
}