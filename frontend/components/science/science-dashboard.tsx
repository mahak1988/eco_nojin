"use client";

import { useEffect, useMemo, useState } from "react";
import { BookOpen, Database, FlaskConical, CheckCircle2, XCircle, Copy, Check } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton, SkeletonTable } from "@/components/ui/skeleton";
import { ChartCard, Hydrograph, RainfallChart, WaterBalanceChart } from "@/components/charts";
import { DataTable, type Column } from "@/components/ui/data-table";
import { ErrorState } from "@/components/shared/ApiState";
import { api } from "@/lib/api-client";

interface Dataset {
  id: string;
  name: string;
  domain: string;
  source: string;
  status: string;
  requires: string;
  license: string;
}
interface ModelCard {
  slug: string;
  fidelity: string | null;
  domain: string | null;
  card: { validity: string; limitations: string };
}

interface Citation {
  slug: string;
  name_fa: string;
  name_en: string;
  reference: string;
  citation: string;
  doi: string | null;
  note: string;
}

// نمونه نمایشی (برچسب‌دار) برای هیدروگراف — خروجی واقعی پس از اتصال کامل ERA5
const DEMO_HYDRO = [
  { t: "00", q: 0.4 }, { t: "04", q: 0.9 }, { t: "08", q: 2.1 }, { t: "12", q: 3.4 },
  { t: "16", q: 2.6 }, { t: "20", q: 1.2 }, { t: "24", q: 0.5 },
];
const DEMO_RAIN = [
  { d: "شنبه", mm: 12 }, { d: "یکشنبه", mm: 8 }, { d: "دوشنبه", mm: 0 },
  { d: "سه‌شنبه", mm: 3 }, { d: "چهارشنبه", mm: 0 }, { d: "پنجشنبه", mm: 18 }, { d: "جمعه", mm: 4 },
];

export function ScienceDashboard() {
  const [datasets, setDatasets] = useState<Dataset[] | null>(null);
  const [citations, setCitations] = useState<Citation[] | null>(null);
  const [modelCards, setModelCards] = useState<ModelCard[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [dRes, cRes, mRes] = await Promise.all([
          api.get<{ datasets?: Dataset[] }>("/api/v1/science/datasets"),
          api.get<{ items?: Citation[] }>("/api/v1/science/citations/index"),
          api.get<{ cards?: ModelCard[] }>("/api/v1/science/model-cards"),
        ]);
        if (!dRes.success || !cRes.success || !mRes.success) {
          throw new Error(dRes.error || cRes.error || mRes.error || "دریافت داده‌های علمی ناموفق بود");
        }
        if (!alive) return;
        setDatasets(dRes.data?.datasets ?? []);
        setCitations(cRes.data?.items ?? []);
        setModelCards(mRes.data?.cards ?? []);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : String(e));
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const datasetColumns: Column<Dataset>[] = [
  { key: "name", header: "نام", searchable: true, sortable: true },
  { key: "domain", header: "حوزه", searchable: true },
  { key: "source", header: "منبع", searchable: true },
  {
    key: "license",
    header: "مجوز",
    render: (d) => <span className="text-muted-foreground">{d.license}</span>,
  },
  {
    key: "status",
    header: "وضعیت",
    sortable: true,
    render: (d) =>
      d.status === "live" ? (
        <Badge variant="secondary" className="gap-1 bg-emerald-500/15 text-emerald-700">
          <CheckCircle2 className="h-3 w-3" />زنده
        </Badge>
      ) : (
        <Badge variant="outline" className="gap-1 text-amber-600">
          <XCircle className="h-3 w-3" />آفلاین
        </Badge>
      ),
  },
];

const DEMO_BALANCE = [
  { t: "فروردین", inflow: 42, outflow: 18, storage: 24 },
  { t: "اردیبهشت", inflow: 30, outflow: 22, storage: 32 },
  { t: "خرداد", inflow: 12, outflow: 26, storage: 18 },
  { t: "تیر", inflow: 4, outflow: 14, storage: 8 },
  { t: "مرداد", inflow: 2, outflow: 8, storage: 2 },
  { t: "شهریور", inflow: 8, outflow: 6, storage: 4 },
];

const liveCount = useMemo(() => (datasets ?? []).filter((d) => d.status === "live").length, [datasets]);

  const copyCitation = async (c: Citation) => {
    try {
      await navigator.clipboard.writeText(c.citation);
      setCopied(c.slug);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      {/* KPI */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">مدل‌های علمی</CardTitle>
            <FlaskConical className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{citations ? citations.length : <Skeleton className="h-7 w-10" />}</div>
            <p className="text-xs text-muted-foreground">ثبت‌شده در موتور HyDroMa</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">دیتاست‌ها</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{datasets ? datasets.length : <Skeleton className="h-7 w-10" />}</div>
            <p className="text-xs text-muted-foreground">منابع داده پلتفرم</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">منابع زنده</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{datasets ? liveCount : <Skeleton className="h-7 w-10" />}</div>
            <p className="text-xs text-muted-foreground">بدون نیاز به اعتبارنامه</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">استنادها</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{citations ? citations.length : <Skeleton className="h-7 w-10" />}</div>
            <p className="text-xs text-muted-foreground">آماده کپی در مقالات</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="هیدروگراف نمونه" description="نمایش شماتیک — پس از فعال‌سازی ERA5 با داده واقعی جایگزین می‌شود">
          <Hydrograph data={DEMO_HYDRO} />
        </ChartCard>
        <ChartCard title="بارش روزانه نمونه" description="نمایش شماتیک — پس از فعال‌سازی ERA5 با داده واقعی جایگزین می‌شود">
          <RainfallChart data={DEMO_RAIN} />
        </ChartCard>
        <ChartCard title="تراز آبی سالانه نمونه" description="نمایش شماتیک — پس از فعال‌سازی ERA5 با داده واقعی جایگزین می‌شود">
          <WaterBalanceChart data={DEMO_BALANCE} />
        </ChartCard>
      </div>

      {/* Datasets */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">کاتالوگ دیتاست‌ها</CardTitle>
          <CardDescription>وضعیت صادقانه؛ دیتاست‌های آفلاین فقط با اعتبارنامه فعال می‌شوند</CardDescription>
        </CardHeader>
        <CardContent>
          {!datasets ? (
            <SkeletonTable rows={4} cols={4} />
          ) : (
            <DataTable<Dataset>
              columns={datasetColumns}
              rows={datasets}
              pageSize={8}
              emptyMessage="دیتاستی یافت نشد"
            />
          )}
        </CardContent>
      </Card>

      {/* Model cards (Phase 9 star 11): limits + validity domain */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FlaskConical className="h-5 w-5" /> کارت‌های مدل (دامنه اعتبار و محدودیت‌ها)
          </CardTitle>
          <CardDescription>
            طبق الگوی HuggingFace — هر مدل با محدودیت‌ها و دامنه اعتبار خود (فاز ۹)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {modelCards === null ? (
            <SkeletonTable rows={3} cols={4} />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {modelCards.map((mc) => (
                <div key={mc.slug} className="rounded-lg border p-3 text-sm">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="font-medium" dir="ltr">{mc.slug}</span>
                    <Badge
                      variant={
                        mc.fidelity === "official"
                          ? "secondary"
                          : mc.fidelity === "simplified"
                            ? "outline"
                            : "destructive"
                      }
                    >
                      {mc.fidelity ?? "—"}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">{mc.domain ?? ""}</p>
                  <p className="mt-2 text-xs leading-5">
                    <span className="font-medium">اعتبار: </span>
                    {mc.card.validity}
                  </p>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">
                    <span className="font-medium">محدودیت: </span>
                    {mc.card.limitations}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Citations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">پیشنهاد استناد برای مدل‌ها</CardTitle>
          <CardDescription>آماده کپی در مقالات؛ DOI پس از اتصال Crossref/OpenAlex اضافه می‌شود</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {!citations ? (
            <div className="space-y-2"><Skeleton className="h-10 w-full" /><Skeleton className="h-10 w-full" /></div>
          ) : (
            citations.map((c) => (
              <div key={c.slug} className="flex items-start justify-between gap-3 rounded-lg border p-3">
                <div className="min-w-0">
                  <div className="text-sm font-medium">{c.name_fa} <span className="text-muted-foreground">({c.name_en})</span></div>
                  <div className="mt-1 text-xs leading-relaxed text-muted-foreground" dir="ltr">{c.citation}</div>
                </div>
                <Button variant="outline" size="sm" className="shrink-0" onClick={() => copyCitation(c)}>
                  {copied === c.slug ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied === c.slug ? "کپی شد" : "کپی"}
                </Button>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
