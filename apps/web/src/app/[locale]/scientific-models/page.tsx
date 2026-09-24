'use client';

import { Button } from '@eco/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@eco/ui/card';
import {
  ArrowRight,
  Award,
  BookOpen,
  ChevronRight,
  Cpu,
  Database,
  ExternalLink,
  FlaskConical,
  Globe,
  Layers,
  Shield,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { PublicLayout } from '@/components/layout';

const modelCategories = [
  {
    icon: FlaskConical,
    title: 'hydroModelsTitle',
    desc: 'hydroModelsDesc',
    count: '24',
    color: 'bg-blue-500/10 text-blue-600',
    ref: 'FAO-56, HEC-RAS, MODFLOW',
  },
  {
    icon: Layers,
    title: 'soilModelsTitle',
    desc: 'soilModelsDesc',
    count: '18',
    color: 'bg-amber-500/10 text-amber-600',
    ref: 'FAO Soil, USDA Taxonomy, PTF',
  },
  {
    icon: Globe,
    title: 'climateModelsTitle',
    desc: 'climateModelsDesc',
    count: '15',
    color: 'bg-cyan-500/10 text-cyan-600',
    ref: 'ERA5, IPCC AR6, CMIP6',
  },
  {
    icon: BookOpen,
    title: 'carbonModelsTitle',
    desc: 'carbonModelsDesc',
    count: '12',
    color: 'bg-green-500/10 text-green-600',
    ref: 'IPCC 2019, RothC, VERRA',
  },
  {
    icon: Cpu,
    title: 'economicsModelsTitle',
    desc: 'economicsModelsDesc',
    count: '10',
    color: 'bg-violet-500/10 text-violet-600',
    ref: 'FAO Econ, CBA, MCA',
  },
  {
    icon: Database,
    title: 'optimizationModelsTitle',
    desc: 'optimizationModelsDesc',
    count: '8',
    color: 'bg-orange-500/10 text-orange-600',
    ref: 'LP/MIP, NSGA-II, MOEA/D',
  },
];

const featuredModels = [
  {
    name: 'Richards Equation Solver',
    category: 'Hydrology',
    desc: 'featured1Desc',
    standard: 'ISO 14064-2',
    language: 'C++',
    status: 'validated',
    ref: 'FAO Irrigation Paper 56',
  },
  {
    name: 'Penman-Monteith ET0',
    category: 'Climate',
    desc: 'featured2Desc',
    standard: 'FAO-56',
    language: 'C++',
    status: 'validated',
    ref: 'FAO Irrigation Paper 56',
  },
  {
    name: 'RothC Carbon Model',
    category: 'Carbon',
    desc: 'featured3Desc',
    standard: 'IPCC 2019 Refinement',
    language: 'Python',
    status: 'validated',
    ref: 'IPCC 2019, RothC v26.3',
  },
  {
    name: 'AquaCrop Yield Model',
    category: 'Crop',
    desc: 'featured4Desc',
    standard: 'FAO AquaCrop v7',
    language: 'Python',
    status: 'partial',
    ref: 'FAO AquaCrop, Steduto et al. 2009',
  },
  {
    name: 'RUSLE Erosion Model',
    category: 'Soil',
    desc: 'featured5Desc',
    standard: 'USDA Handbook 703',
    language: 'C++',
    status: 'validated',
    ref: 'Renard et al. 1997, USDA',
  },
  {
    name: 'MODFLOW Groundwater',
    category: 'Hydrogeology',
    desc: 'featured6Desc',
    standard: 'USGS MODFLOW-2005',
    language: 'Fortran/C++',
    status: 'validated',
    ref: 'Harbaugh 2005, USGS',
  },
];

const standardsTable = [
  {
    domain: 'Hydrology',
    standard: 'ISO 14064-2, FAO-56',
    org: 'ISO/FAO',
    version: '2019/1998',
    adoption: 'Full',
  },
  {
    domain: 'Soil Science',
    standard: 'USDA Taxonomy, WRB',
    org: 'USDA/IUSS',
    version: '2022/2015',
    adoption: 'Full',
  },
  {
    domain: 'Climate',
    standard: 'IPCC AR6, CMIP6',
    org: 'IPCC/WCRP',
    version: '2021/2020',
    adoption: 'Full',
  },
  {
    domain: 'Carbon Accounting',
    standard: 'IPCC 2019, GHG Protocol',
    org: 'IPCC/WRI',
    version: '2019/2015',
    adoption: 'Full',
  },
  {
    domain: 'Geospatial',
    standard: 'OGC API, STAC',
    org: 'OGC',
    version: '2023/2021',
    adoption: 'Partial',
  },
  {
    domain: 'Economics',
    standard: 'FAO CBA Guidelines',
    org: 'FAO',
    version: '2020',
    adoption: 'Partial',
  },
];

export default function ScientificModelsPage() {
  const t = useTranslations('scientificModels');

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

          {/* Model Categories */}
          <section className="mb-16">
            <h2 className="mb-8 text-3xl font-bold tracking-tight text-center">
              {t('categoriesTitle')}
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {modelCategories.map((cat, index) => (
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
                      <span className="text-sm text-muted-foreground">{t('modelsCount')}</span>
                    </div>
                    <div className="mb-4 text-sm text-muted-foreground">
                      <span className="font-medium">{t('standards')}: </span>
                      {t(cat.ref)}
                    </div>
                    <Button variant="ghost" size="sm" asChild className="w-full">
                      <a
                        href={`/fa/scientific-models/${cat.title.toLowerCase().replace(/\s+/g, '-')}`}
                      >
                        {t('viewModels')}
                        <ArrowRight className="size-4 ml-1" aria-hidden="true" />
                      </a>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          {/* Featured Models */}
          <section className="mb-16">
            <div className="mb-8 flex items-center justify-between">
              <h2 className="text-3xl font-bold tracking-tight">{t('featuredTitle')}</h2>
              <Button variant="outline" size="sm" asChild>
                <a href="/fa/scientific-models/catalog">
                  {t('viewAll')}
                  <ExternalLink className="size-4 ml-1" aria-hidden="true" />
                </a>
              </Button>
            </div>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {featuredModels.map((model, index) => (
                <Card key={index} className="h-full hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <span
                          className={`rounded-full border px-2 py-0.5 text-xs ${
                            model.status === 'validated'
                              ? 'border-green-200 bg-green-50 text-green-700'
                              : 'border-amber-200 bg-amber-50 text-amber-700'
                          }`}
                        >
                          {t(model.status)}
                        </span>
                      </div>
                      <span className="rounded-full border border-border bg-background px-2 py-0.5 text-xs text-muted-foreground">
                        {model.language}
                      </span>
                    </div>
                    <CardTitle>{model.name}</CardTitle>
                    <CardDescription>{t(model.desc)}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="mb-3 text-sm text-muted-foreground">
                      <span className="font-medium">{t('category')}: </span>
                      {t(model.category)}
                    </p>
                    <p className="mb-4 text-sm text-muted-foreground">
                      <span className="font-medium">{t('standard')}: </span>
                      {model.standard}
                    </p>
                    <p className="mb-4 text-xs text-muted-foreground">
                      <span className="font-medium">{t('reference')}: </span>
                      {model.ref}
                    </p>
                    <Button variant="ghost" size="sm" asChild className="w-full">
                      <a
                        href={`/fa/scientific-models/${model.name.toLowerCase().replace(/\s+/g, '-')}`}
                      >
                        {t('viewDetails')}
                        <ChevronRight className="size-4 ml-1" aria-hidden="true" />
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
              {t('standardsTitle')}
            </h2>
            <div className="rounded-xl border border-border bg-background overflow-hidden font-mono text-sm">
              <div className="grid grid-cols-5 border-b border-border bg-muted/50 px-6 py-4 text-xs font-medium text-muted-foreground">
                <div className="col-span-2">{t('stdCol1')}</div>
                <div>{t('stdCol2')}</div>
                <div className="hidden md:block">{t('stdCol3')}</div>
                <div>{t('stdCol4')}</div>
                <div>{t('stdCol5')}</div>
              </div>
              {standardsTable.map((std, index) => (
                <div
                  key={index}
                  className="grid grid-cols-5 border-b border-border px-6 py-4 last:border-0 items-center hover:bg-muted/50 transition-colors"
                >
                  <div className="col-span-2 font-medium">{t(std.domain)}</div>
                  <div className="text-sm text-muted-foreground">{std.standard}</div>
                  <div className="hidden md:block text-sm text-muted-foreground">{std.org}</div>
                  <div className="text-sm text-muted-foreground">{std.version}</div>
                  <div>
                    <span
                      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                        std.adoption === 'Full'
                          ? 'border-green-200 bg-green-50 text-green-700'
                          : 'border-amber-200 bg-amber-50 text-amber-700'
                      }`}
                    >
                      <span
                        className="mr-1.5 h-1.5 w-1.5 rounded-full bg-current"
                        aria-hidden="true"
                      />
                      {t(std.adoption.toLowerCase())}
                    </span>
                  </div>
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
                <a href="/fa/dashboard">
                  <span className="inline-flex items-center gap-2">
                    <span>{t('ctaDashboard')}</span>
                    <ArrowRight className="size-4" />
                  </span>
                </a>
              </Button>
              <Button variant="outline" size="lg" className="w-full sm:w-auto" asChild>
                <a href="/fa/docs/api">{t('ctaApiDocs')}</a>
              </Button>
            </div>
          </section>
        </div>
      </div>
    </PublicLayout>
  );
}
