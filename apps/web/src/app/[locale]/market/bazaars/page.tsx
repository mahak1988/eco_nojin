import { Metadata } from 'next';
import { getTranslations, setRequestLocale } from 'next-intl/server';
import { BazaarEstablishmentWizard } from '@/components/BazaarEstablishmentWizard';
import { FivePart } from '@/components/FivePart';
import { MarketMap } from '@/components/MarketMap';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { SiteNav } from '@/components/SiteNav';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://econojin.example.org';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  return {
    title: `بازارچه · پایهٔ ۳`,
    description: 'تأسیس بازارچه نهادی — ۱۰ گام، امضای دیجیتال ۵ طرف',
    openGraph: {
      type: 'website',
      locale,
      url: `${BASE_URL}/${locale}/market/bazaars`,
      title: `بازارچه · پایهٔ ۳`,
      description: 'تأسیس بازارچه نهادی — ۱۰ گام، امضای دیجیتال ۵ طرف',
      images: [
        { url: `${BASE_URL}/og-bazaar.png`, width: 1200, height: 630, alt: 'Eco Nojin Bazaar' },
      ],
    },
    alternates: {
      canonical: `${BASE_URL}/${locale}/market/bazaars`,
      languages: { fa: `${BASE_URL}/fa/market/bazaars`, en: `${BASE_URL}/en/market/bazaars` },
    },
  };
}

export default async function BazaarsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />

      <section className="mx-auto max-w-5xl px-6 pb-6 pt-2">
        <ProvenanceStamp source="phase3-bazaar-institution" label="پایهٔ ۳ — بازارچه نهاد">
          <h1 className="display text-4xl font-bold text-ink">
            {t('market.bazaarTitle') ?? 'تأسیس بازارچه نهادی'}
          </h1>
        </ProvenanceStamp>
        <p className="mt-3 max-w-2xl text-ink-soft">
          {locale === 'fa'
            ? '۱۰ گام تأسیس بازارچه — هیئت ۵ نفره — امضای دیجیتال PQ (DILITHIUM2+ED25519, KYBER512+X25519)'
            : '10-step bazaar establishment — 5-member founding board — PQ digital signatures (5-party)'}
        </p>
      </section>

      {/* SCAFFOLD NOTICE */}
      <section className="mx-auto max-w-5xl px-6 pb-4">
        <div
          className="card border-amber-400/40 p-4 text-amber-700 text-sm"
          style={{ borderColor: 'color-mix(in oklch, oklch(0.73 0.18) 40%, var(--line))' }}
        >
          <strong>SCAFFOLD:</strong> This is Phase 3 preparation scaffolding. Bazaar data, server
          actions, and MapLibre tiles are placeholders. Full market-live delivery requires Phase 3
          backend endpoints, PostGIS extension, and MapLibre style configuration.
        </div>
      </section>

      {/* T05 five-part structure (§6.1) */}
      <section className="mx-auto max-w-5xl px-6 pb-6">
        <FivePart
          title={locale === 'fa' ? 'چرا بازارچه نهادی؟' : 'Why Institutional Bazaar?'}
          lead={
            locale === 'fa'
              ? 'پایهٔ ۳: تأسیس بازارچه نهادی با ۱۰ گام و امضای دیجیتال ۵ طرف.'
              : 'Phase 3: Institutional bazaar with 10 steps and 5-party digital signatures.'
          }
          what={
            locale === 'fa'
              ? 'بازارچه نهاد، ساختار رسمی برای ۴۲ بازار و ۳۸ فروشگاه در منطقه فراهم می‌کند.'
              : 'Institutional bazaar provides formal structure for 42 bazaars and 38 stores in the region.'
          }
          audience={
            locale === 'fa'
              ? 'مدیران منظر، روستاهای فعال، و نهادهای نظارتی'
              : 'Landscape managers, active villages, and oversight bodies'
          }
          evidence={[
            '§5.2 — 42 bazaars + 38 stores per regional plan',
            '§6.2 — 5-party PQ digital signature per bazaar',
            '§7 — 10-step establishment wizard',
          ]}
          limits={[
            'Scaffold: no live data until Phase 3 backend',
            'MapLibre tiles: placeholder style until Phase 3',
            'Digital signatures: PQ crypto not enforced until Phase 3',
          ]}
          next={[
            'Phase 3: API endpoints for bazaar CRUD',
            'Phase 3: PostGIS extension + geometry storage',
            'Phase 3: RLS policies for multi-tenant isolation',
          ]}
          evidenceLabel={locale === 'fa' ? 'پایه‌ها' : 'Evidence'}
          limitsLabel={locale === 'fa' ? 'محدودیت‌ها' : 'Limits'}
          nextLabel={locale === 'fa' ? 'گام بعدی' : 'Next'}
        />
      </section>

      {/* Wizard (T05, 10 steps) */}
      <section className="mx-auto max-w-5xl px-6 pb-6">
        <BazaarEstablishmentWizard locale={locale} />
      </section>

      {/* Map (reusable regional hub) */}
      <section className="mx-auto max-w-5xl px-6 pb-16">
        <h2 className="text-sm font-semibold text-ink-soft mb-3">
          {locale === 'fa' ? 'نقشه بازارها' : 'Bazaar Map'}
        </h2>
        <MarketMap bazaars={[]} locale={locale} height={400} />
      </section>
    </main>
  );
}
