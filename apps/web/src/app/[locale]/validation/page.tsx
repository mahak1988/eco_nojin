'use client';

import { Button } from '@eco/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@eco/ui/card';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle,
  ChevronRight,
  ExternalLink,
  Microscope,
  Shield,
  Target,
  TrendingUp,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { PublicLayout } from '@/components/layout';

const validationTypes = [
  {
    icon: Microscope,
    title: 'benchValidationTitle',
    desc: 'benchValidationDesc',
    count: '156',
    color: 'bg-blue-500/10 text-blue-600',
    standard: 'ISO 17025',
  },
  {
    icon: BarChart3,
    title: 'fieldValidationTitle',
    desc: 'fieldValidationDesc',
    count: '89',
    color: 'bg-green-500/10 text-green-600',
    standard: 'FAO Guidelines',
  },
  {
    icon: TrendingUp,
    title: 'statValidationTitle',
    desc: 'statValidationDesc',
    count: '234',
    color: 'bg-purple-500/10 text-purple-600',
    standard: 'WMO Standards',
  },
  {
    icon: Target,
    title: 'uncertaintyTitle',
    desc: 'uncertaintyDesc',
    count: '67',
    color: 'bg-orange-500/10 text-orange-600',
    standard: 'JCGM 100:2008',
  },
  {
    icon: Shield,
    title: 'peerReviewTitle',
    desc: 'peerReviewDesc',
    count: '42',
    color: 'bg-red-500/10 text-red-600',
    standard: 'COPE Guidelines',
  },
  {
    icon: CheckCircle,
    title: 'regulatoryTitle',
    desc: 'regulatoryDesc',
    count: '28',
    color: 'bg-cyan-500/10 text-cyan-600',
    standard: 'National Laws',
  },
];

const validationResults = [
  {
    model: 'Richards Equation',
    metric: 'val1Metric',
    rmse: '0.023',
    r2: '0.987',
    nse: '0.965',
    bias: '0.001',
    status: 'validated',
    sites: 12,
  },
  {
    model: 'Penman-Monteith ET0',
    metric: 'val2Metric',
    rmse: '0.156',
    r2: '0.992',
    nse: '0.978',
    bias: '-0.008',
    status: 'validated',
    sites: 24,
  },
  {
    model: 'RothC Carbon',
    metric: 'val3Metric',
    rmse: '1.23',
    r2: '0.945',
    nse: '0.912',
    bias: '0.034',
    status: 'validated',
    sites: 18,
  },
  {
    model: 'AquaCrop Yield',
    metric: 'val4Metric',
    rmse: '0.412',
    r2: '0.892',
    nse: '0.856',
    bias: '-0.067',
    status: 'partial',
    sites: 15,
  },
  {
    model: 'RUSLE Erosion',
    metric: 'val5Metric',
    rmse: '2.34',
    r2: '0.876',
    nse: '0.823',
    bias: '0.123',
    status: 'validated',
    sites: 22,
  },
  {
    model: 'MODFLOW GW',
    metric: 'val6Metric',
    rmse: '0.567',
    r2: '0.934',
    nse: '0.898',
    bias: '-0.023',
    status: 'validated',
    sites: 31,
  },
];

const validationMethods = [
  { title: 'method1Title', desc: 'method1Desc', icon: Microscope, standard: 'ISO 17025' },
  { title: 'method2Title', desc: 'method2Desc', icon: BarChart3, standard: 'FAO-56 Ch.8' },
  { title: 'method3Title', desc: 'method3Desc', icon: TrendingUp, standard: 'WMO-No.8' },
  { title: 'method4Title', desc: 'method4Desc', icon: Target, standard: 'JCGM 100:2008' },
  { title: 'method5Title', desc: 'method5Desc', icon: Shield, standard: 'COPE' },
  { title: 'method6Title', desc: 'method6Desc', icon: CheckCircle, standard: 'National' },
];

const ongoingValidation = [
  {
    title: 'ongoing1Title',
    model: 'AquaCrop v7',
    status: 'In Progress',
    progress: 65,
    target: 'Q2 2025',
  },
  {
    title: 'ongoing2Title',
    model: 'New GW Model',
    status: 'Planning',
    progress: 10,
    target: 'Q4 2025',
  },
  {
    title: 'ongoing3Title',
    model: 'Carbon v2',
    status: 'Data Collection',
    progress: 35,
    target: 'Q3 2025',
  },
];

export default function ValidationPage() {
  const t = useTranslations('validation');

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

          {/* Validation Types */}
          <section className="mb-16">
            <h2 className="mb-8 text-3xl font-bold tracking-tight text-center">
              {t('typesTitle')}
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {validationTypes.map((type, index) => (
                <Card key={index} className="h-full hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <div
                      className={`flex h-14 w-14 items-center justify-center rounded-xl ${type.color}`}
                    >
                      <type.icon className="size-7" aria-hidden="true" />
                    </div>
                    <CardTitle>{t(type.title)}</CardTitle>
                    <CardDescription>{t(type.desc)}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="mb-4 flex items-center justify-between">
                      <span className="text-3xl font-bold text-primary">{type.count}</span>
                      <span className="text-sm text-muted-foreground">{t('testsCount')}</span>
                    </div>
                    <div className="mb-4 text-sm text-muted-foreground">
                      <span className="font-medium">{t('standard')}: </span>
                      {type.standard}
                    </div>
                    <Button variant="ghost" size="sm" asChild className="w-full">
                      <a href={`/fa/validation/${type.title.toLowerCase().replace(/\s+/g, '-')}`}>
                        {t('viewDetails')}
                        <ChevronRight className="size-4 ml-1" aria-hidden="true" />
                      </a>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          {/* Validation Results */}
          <section className="mb-16">
            <div className="mb-8 flex items-center justify-between">
              <h2 className="text-3xl font-bold tracking-tight">{t('resultsTitle')}</h2>
              <Button variant="outline" size="sm" asChild>
                <a href="/fa/validation/results">
                  {t('viewAll')}
                  <ExternalLink className="size-4 ml-1" aria-hidden="true" />
                </a>
              </Button>
            </div>
            <div className="rounded-xl border border-border bg-background overflow-hidden font-mono text-sm">
              <div className="grid grid-cols-7 border-b border-border bg-muted/50 px-6 py-4 text-xs font-medium text-muted-foreground">
                <div className="col-span-2">{t('resCol1')}</div>
                <div>{t('resCol2')}</div>
                <div>{t('resCol3')}</div>
                <div>{t('resCol4')}</div>
                <div>{t('resCol5')}</div>
                <div>{t('resCol6')}</div>
              </div>
              {validationResults.map((result, index) => (
                <div
                  key={index}
                  className="grid grid-cols-7 border-b border-border px-6 py-4 last:border-0 items-center hover:bg-muted/50 transition-colors"
                >
                  <div className="col-span-2 font-medium">{result.model}</div>
                  <div className="text-sm text-muted-foreground">{t(result.metric)}</div>
                  <div className="text-sm text-muted-foreground">{result.rmse}</div>
                  <div className="text-sm text-muted-foreground">{result.r2}</div>
                  <div className="text-sm text-muted-foreground">{result.nse}</div>
                  <div className="text-sm text-muted-foreground">{result.bias}</div>
                  <div>
                    <span
                      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                        result.status === 'validated'
                          ? 'border-green-200 bg-green-50 text-green-700'
                          : 'border-amber-200 bg-amber-50 text-amber-700'
                      }`}
                    >
                      <span
                        className="mr-1.5 h-1.5 w-1.5 rounded-full bg-current"
                        aria-hidden="true"
                      />
                      {t(result.status)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Validation Methods */}
          <section className="mb-16">
            <h2 className="mb-8 text-3xl font-bold tracking-tight text-center">
              {t('methodsTitle')}
            </h2>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {validationMethods.map((method, index) => (
                <Card key={index} className="h-full hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                      <method.icon className="size-6" aria-hidden="true" />
                    </div>
                    <CardTitle>{t(method.title)}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="mb-3 text-muted-foreground">{t(method.desc)}</p>
                    <div className="text-xs text-muted-foreground">
                      <span className="font-medium">{t('standard')}: </span>
                      {method.standard}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          {/* Ongoing Validation */}
          <section className="mb-16">
            <h2 className="mb-8 text-3xl font-bold tracking-tight text-center">
              {t('ongoingTitle')}
            </h2>
            <div className="grid gap-6 md:grid-cols-3">
              {ongoingValidation.map((ongoing, index) => (
                <Card key={index} className="h-full">
                  <CardHeader>
                    <CardTitle>{t(ongoing.title)}</CardTitle>
                    <CardDescription>{ongoing.model}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">{ongoing.status}</span>
                        <span className="text-sm text-muted-foreground">{ongoing.progress}%</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-border overflow-hidden">
                        <div
                          className="h-full rounded-full bg-primary transition-all"
                          style={{ width: `${ongoing.progress}%` }}
                        />
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      <span className="font-medium">{t('target')}: </span>
                      {ongoing.target}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          {/* CTA */}
          <section className="text-center">
            <h2 className="mb-4 text-2xl font-bold tracking-tight">{t('ctaTitle')}</h2>
            <p className="mb-8 text-muted-foreground max-w-2xl mx-auto">{t('ctaDesc')}</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="w-full sm:w-auto gap-2" asChild>
                <a href="/fa/validation/reports">
                  <span className="inline-flex items-center gap-2">
                    <span>{t('ctaReports')}</span>
                    <ArrowRight className="size-4" />
                  </span>
                </a>
              </Button>
              <Button variant="outline" size="lg" className="w-full sm:w-auto" asChild>
                <a href="/fa/contact?topic=validation">{t('ctaContact')}</a>
              </Button>
            </div>
          </section>
        </div>
      </div>
    </PublicLayout>
  );
}
