'use client';

import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface Partner {
  name: string;
  type: 'technical' | 'academic' | 'government' | 'commercial';
  description: string;
  website: string;
  logo?: string;
  since: string;
}

const PARTNERS: Partner[] = [
  {
    name: 'FAO',
    type: 'government',
    description: 'Food and Agriculture Organization - Data standards and methodology alignment',
    website: 'https://fao.org',
    since: '2023-01-15',
  },
  {
    name: 'IPCC',
    type: 'academic',
    description: 'Intergovernmental Panel on Climate Change - Carbon accounting standards',
    website: 'https://ipcc.ch',
    since: '2023-03-22',
  },
  {
    name: 'OGC',
    type: 'technical',
    description: 'Open Geospatial Consortium - Geospatial data interoperability',
    website: 'https://ogc.org',
    since: '2023-06-10',
  },
  {
    name: 'Alchemy',
    type: 'technical',
    description: 'Blockchain infrastructure provider for carbon registry',
    website: 'https://alchemy.com',
    since: '2024-01-20',
  },
  {
    name: 'Supabase',
    type: 'technical',
    description: 'PostgreSQL platform for real-time data and auth',
    website: 'https://supabase.com',
    since: '2023-09-01',
  },
];

const typeLabels = {
  technical: 'Technical',
  academic: 'Academic',
  government: 'Government',
  commercial: 'Commercial',
};

const typeColors = {
  technical: 'text-water bg-water/10',
  academic: 'text-forest bg-forest/10',
  government: 'text-copper bg-copper/10',
  commercial: 'text-amber bg-amber/10',
};

export default function PartnersPage() {
  const t = useTranslations('developers.partners');
  const common = useTranslations('common');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <header className="mb-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('lead')}</p>
        </header>

        <div className="grid gap-6">
          {PARTNERS.map((partner) => (
            <Card key={partner.name} density="cozy">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
                <div className="flex items-start gap-4">
                  {partner.logo && (
                    <img src={partner.logo} alt={partner.name} className="w-12 h-12 rounded-lg object-cover" />
                  )}
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-xl font-semibold text-ink">{partner.name}</h3>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${typeColors[partner.type]}`}>
                        {t(`partnerType.${partner.type}`)}
                      </span>
                    </div>
                    <p className="text-ink-soft mb-2">{partner.description}</p>
                    <a
                      href={partner.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-water hover:underline"
                    >
                      {partner.website}
                    </a>
                  </div>
                </div>
                <div className="text-right sm:text-left">
                  <p className="text-sm text-ink-soft">
                    {t('partnerSince')} {new Date(partner.since).toLocaleDateString(locale === 'fa' ? 'fa-IR' : 'en-US', { year: 'numeric', month: 'long' })}
                  </p>
                </div>
              </div>
              <ProvenanceStamp source="Partner Registry" verified={true} timestamp={partner.since} />
            </Card>
          ))}
        </div>

        <Card density="cozy" className="mt-6">
          <h2 className="font-medium text-ink mb-3">{t('becomePartner')}</h2>
          <p className="text-sm text-ink-soft mb-4">{t('becomePartnerDesc')}</p>
          <a
            href="mailto:partners@econojin.example.org"
            className="text-sm text-water hover:underline"
          >
            {t('contactUs')}
          </a>
        </Card>

        <div className="mt-6 grid gap-4">
          <Card density="cozy" className="border-clay/40 bg-clay/5">
            <h3 className="font-medium text-ink mb-2">{t('limitsTitle')}</h3>
            <ul className="space-y-1 text-sm text-ink-soft">
              {t.raw('limits')?.map((item: string, idx: number) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-copper">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>
          <Card density="cozy" className="border-forest/40 bg-forest/5">
            <h3 className="font-medium text-ink mb-2">{t('nextTitle')}</h3>
            <ul className="space-y-1 text-sm text-ink-soft">
              {t.raw('next')?.map((item: string, idx: number) => (
                <li key={idx} className="flex gap-2">
                  <span className="text-forest">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </main>
  );
}