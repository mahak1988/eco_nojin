'use client';

import { Button } from '@eco/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@eco/ui/card';
import {
  ArrowRight,
  Award,
  BookOpen,
  ChevronRight,
  Database,
  ExternalLink,
  FileText,
  Globe,
  Layers,
  Shield,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { PublicLayout } from '@/components/layout';

const referenceCategories = [
  {
    icon: BookOpen,
    title: 'faoRefsTitle',
    desc: 'faoRefsDesc',
    count: '42',
    color: 'bg-blue-500/10 text-blue-600',
    items: ['FAO-56', 'FAO Soil Bulletin', 'AquaCrop', 'GAEZ'],
  },
  {
    icon: Globe,
    title: 'ipccRefsTitle',
    desc: 'ipccRefsDesc',
    count: '38',
    color: 'bg-green-500/10 text-green-600',
    items: ['IPCC AR6', 'IPCC 2019 Refinement', 'GHG Protocol', 'Good Practice Guidance'],
  },
  {
    icon: Layers,
    title: 'ogcRefsTitle',
    desc: 'ogcRefsDesc',
    count: '25',
    color: 'bg-purple-500/10 text-purple-600',
    items: ['OGC API Features', 'OGC API Coverages', 'STAC', 'GeoJSON'],
  },
  {
    icon: FileText,
    title: 'isoRefsTitle',
    desc: 'isoRefsDesc',
    count: '18',
    color: 'bg-orange-500/10 text-orange-600',
    items: ['ISO 14064-2', 'ISO 14001', 'ISO 19115', 'ISO 19157'],
  },
  {
    icon: Award,
    title: 'verraRefsTitle',
    desc: 'verraRefsDesc',
    count: '15',
    color: 'bg-red-500/10 text-red-600',
    items: ['VCS Standard', 'VM0042', 'VM0017', 'CCB Standards'],
  },
  {
    icon: Database,
    title: 'dataRefsTitle',
    desc: 'dataRefsDesc',
    count: '30',
    color: 'bg-cyan-500/10 text-cyan-600',
    items: ['ERA5', 'Copernicus CGLS', 'ESA CCI', 'HydroSHEDS'],
  },
];

const keyDocuments = [
  {
    title: 'doc1Title',
    org: 'FAO',
    year: '2023',
    type: 'doc1Type',
    desc: 'doc1Desc',
    url: 'https://fao.org/documents/56',
    status: 'active',
  },
  {
    title: 'doc2Title',
    org: 'IPCC',
    year: '2021',
    type: 'doc2Type',
    desc: 'doc2Desc',
    url: 'https://ipcc.ch/report/ar6',
    status: 'active',
  },
  {
    title: 'doc3Title',
    org: 'OGC',
    year: '2023',
    type: 'doc3Type',
    desc: 'doc3Desc',
    url: 'https://ogc.org/standards',
    status: 'active',
  },
  {
    title: 'doc4Title',
    org: 'ISO',
    year: '2019',
    type: 'doc4Type',
    desc: 'doc4Desc',
    url: 'https://iso.org/standard/66652',
    status: 'active',
  },
  {
    title: 'doc5Title',
    org: 'Verra',
    year: '2022',
    type: 'doc5Type',
    desc: 'doc5Desc',
    url: 'https://verra.org/methodologies',
    status: 'active',
  },
  {
    title: 'doc6Title',
    org: 'WMO',
    year: '2020',
    type: 'doc6Type',
    desc: 'doc6Desc',
    url: 'https://wmo.int/era5',
    status: 'active',
  },
];

const standardsCompliance = [
  {
    standard: 'FAO-56',
    domain: 'Irrigation',
    compliance: 'Full',
    lastAudit: '2024-01',
    notes: 'Full implementation with dual Kc approach',
  },
  {
    standard: 'IPCC 2019 Refinement',
    domain: 'Carbon Accounting',
    compliance: 'Full',
    lastAudit: '2024-03',
    notes: 'Tier 2/3 methods implemented',
  },
  {
    standard: 'ISO 14064-2',
    domain: 'GHG Projects',
    compliance: 'Full',
    lastAudit: '2023-11',
    notes: 'Project-level quantification',
  },
  {
    standard: 'OGC API Features',
    domain: 'Geospatial API',
    compliance: 'Partial',
    lastAudit: '2024-02',
    notes: 'Core conformance classes met',
  },
  {
    standard: 'STAC Spec',
    domain: 'Catalog Standard',
    compliance: 'Full',
    lastAudit: '2024-01',
    notes: 'STAC 1.0.0 compliant',
  },
  {
    standard: 'VERRA VM0042',
    domain: 'IFM Methodology',
    compliance: 'Partial',
    lastAudit: '2023-12',
    notes: 'Applicability conditions met',
  },
];

export default function ReferencesPage() {
  const t = useTranslations('references');

  return (
    <PublicLayout>
      <div className="py-16 md:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Hero */}
          <section className="mb-16 text-center">
            <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
              {t('heroTitle')}
            </h1>
            <p className="mx-auto max-w-3xl text-lg text-muted-foreground">{t('heroDesc')}</p>
          </section>

          {/* Reference Categories */}
          <section className="mb-16">
            <h2 className="mb-8 text-3xl font-bold tracking-tight text-center">
              {t('categoriesTitle')}
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {referenceCategories.map((cat, index) => (
                <Card key={index} className="h-full hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <div
                      className={`flex h-14 w-14 items-center justify-center rounded-xl ${cat.color}`}
                    >
                      <cat.icon className="size-7" aria-hidden="true" />
                    </div>
                    <CardTitle>{t(cat.title)}</CardTitle>
                    <CardDescription>{t(cat.desc)}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="mb-4 flex items-center justify-between">
                      <span className="text-3xl font-bold text-primary">{cat.count}</span>
                      <span className="text-sm text-muted-foreground">{t('documentsCount')}</span>
                    </div>
                    <div className="mb-4 flex flex-wrap gap-1">
                      {cat.items.map((item, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 rounded bg-muted text-xs font-medium text-muted-foreground"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                    <Button variant="ghost" size="sm" asChild className="w-full">
                      <a href={`/fa/references/${cat.title.toLowerCase().replace(/\s+/g, '-')}`}>
                        {t('viewDocuments')}
                        <ChevronRight className="size-4 ml-1" aria-hidden="true" />
                      </a>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          {/* Key Documents */}
          <section className="mb-16">
            <div className="mb-8 flex items-center justify-between">
              <h2 className="text-3xl font-bold tracking-tight">{t('keyDocsTitle')}</h2>
              <Button variant="outline" size="sm" asChild>
                <a href="/fa/references/library">
                  {t('viewAll')}
                  <ExternalLink className="size-4 ml-1" aria-hidden="true" />
                </a>
              </Button>
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {keyDocuments.map((doc, index) => (
                <Card key={index} className="h-full hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <span
                          className={`rounded-full border px-2 py-0.5 text-xs ${
                            doc.status === 'active'
                              ? 'border-green-200 bg-green-50 text-green-700'
                              : 'border-amber-200 bg-amber-50 text-amber-700'
                          }`}
                        >
                          {t(doc.status)}
                        </span>
                      </div>
                      <span className="rounded-full border border-border bg-background px-2 py-0.5 text-xs text-muted-foreground">
                        {doc.year}
                      </span>
                    </div>
                    <CardTitle>{t(doc.title)}</CardTitle>
                    <CardDescription>{t(doc.desc)}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="mb-3 text-sm text-muted-foreground">
                      <span className="font-medium">{t('organization')}: </span>
                      {doc.org}
                    </p>
                    <p className="mb-3 text-sm text-muted-foreground">
                      <span className="font-medium">{t('type')}: </span>
                      {t(doc.type)}
                    </p>
                    <Button variant="ghost" size="sm" asChild className="w-full">
                      <a href={doc.url} target="_blank" rel="noopener noreferrer">
                        {t('viewDocument')}
                        <ExternalLink className="size-4 ml-1" aria-hidden="true" />
                      </a>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          {/* Standards Compliance */}
          <section className="mb-16">
            <h2 className="mb-8 text-3xl font-bold tracking-tight text-center">
              {t('complianceTitle')}
            </h2>
            <div className="rounded-xl border border-border bg-background overflow-hidden font-mono text-sm">
              <div className="grid grid-cols-6 border-b border-border bg-muted/50 px-6 py-4 text-xs font-medium text-muted-foreground">
                <div className="col-span-2">{t('compCol1')}</div>
                <div>{t('compCol2')}</div>
                <div>{t('compCol3')}</div>
                <div>{t('compCol4')}</div>
                <div>{t('compCol5')}</div>
              </div>
              {standardsCompliance.map((std, index) => (
                <div
                  key={index}
                  className="grid grid-cols-6 border-b border-border px-6 py-4 last:border-0 items-center hover:bg-muted/50 transition-colors"
                >
                  <div className="col-span-2 font-medium">{std.standard}</div>
                  <div className="text-sm text-muted-foreground">{std.domain}</div>
                  <div>
                    <span
                      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                        std.compliance === 'Full'
                          ? 'border-green-200 bg-green-50 text-green-700'
                          : 'border-amber-200 bg-amber-50 text-amber-700'
                      }`}
                    >
                      <span
                        className="mr-1.5 h-1.5 w-1.5 rounded-full bg-current"
                        aria-hidden="true"
                      />
                      {t(std.compliance.toLowerCase())}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">{std.lastAudit}</div>
                  <div className="text-xs text-muted-foreground">{std.notes}</div>
                </div>
              ))}
            </div>
          </section>

          {/* CTA */}
          <section className="text-center">
            <h2 className="mb-4 text-2xl font-bold tracking-tight">{t('ctaTitle')}</h2>
            <p className="mb-8 text-muted-foreground max-w-2xl mx-auto">{t('ctaDesc')}</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="w-full sm:w-auto gap-2" asChild>
                <a href="/fa/docs">
                  <span className="inline-flex items-center gap-2">
                    <span>{t('ctaDocs')}</span>
                    <ArrowRight className="size-4" />
                  </span>
                </a>
              </Button>
              <Button variant="outline" size="lg" className="w-full sm:w-auto" asChild>
                <a href="/fa/contact?topic=references">{t('ctaContact')}</a>
              </Button>
            </div>
          </section>
        </div>
      </div>
    </PublicLayout>
  );
}
