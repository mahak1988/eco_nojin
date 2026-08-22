"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BarChart3,
  Satellite,
  Sprout,
  FlaskConical,
  Coins,
  Leaf,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import { apiUrl } from "@/lib/config";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface OverviewData {
  farms_count: number;
  total_area_hectares: number;
  soil_analyses_count: number;
  satellite_analyses_count: number;
  scenario_runs_count: number;
  carbon_projects_count: number;
}

interface SoilTrendsData {
  data: { date: string | null; health_score: number; ph: number; organic_matter: number }[];
  average_health: number;
  trend: string;
}

interface NdviTrendsData {
  data: { date: string | null; ndvi: number }[];
  average_ndvi: number;
  health_status: string;
}

interface PerformanceData {
  soil_health_distribution: { excellent: number; good: number; moderate: number; poor: number };
  total_soil_analyses: number;
  total_satellite_analyses: number;
}

interface CarbonData {
  total_projects: number;
  total_area_hectares: number;
  total_credits_issued: number;
  projects: { name: string; project_type: string; area_hectares: number; credits_issued: number; status: string }[];
}

const TREND_LABELS: Record<string, string> = {
  improving: "رو به بهبود",
  declining: "رو به افول",
  stable: "پایدار",
  "no data": "بدون داده",
};

export default function AdminAnalytics() {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("auth_token") : null;
  const userJson = typeof window !== "undefined" ? window.localStorage.getItem("auth_user") : null;
  const user = useMemo(() => {
    try {
      return userJson ? JSON.parse(userJson) : null;
    } catch {
      return null;
    }
  }, [userJson]);

  const overview = useQuery({
    queryKey: ["analytics-overview", token],
    queryFn: async (): Promise<OverviewData> => {
      const res = await fetch(apiUrl("/api/v1/analytics/overview"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user),
  });

  const soilTrends = useQuery({
    queryKey: ["analytics-soil-trends", token],
    queryFn: async (): Promise<SoilTrendsData> => {
      const res = await fetch(apiUrl("/api/v1/analytics/soil-trends"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user),
  });

  const ndviTrends = useQuery({
    queryKey: ["analytics-ndvi-trends", token],
    queryFn: async (): Promise<NdviTrendsData> => {
      const res = await fetch(apiUrl("/api/v1/analytics/ndvi-trends"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user),
  });

  const performance = useQuery({
    queryKey: ["analytics-performance", token],
    queryFn: async (): Promise<PerformanceData> => {
      const res = await fetch(apiUrl("/api/v1/analytics/performance-metrics"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user),
  });

  const carbon = useQuery({
    queryKey: ["analytics-carbon", token],
    queryFn: async (): Promise<CarbonData> => {
      const res = await fetch(apiUrl("/api/v1/analytics/carbon-summary"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user),
  });

  if (!token) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-3 p-10 text-center">
          <BarChart3 className="h-10 w-10 text-muted-foreground" />
          <p className="font-semibold text-foreground">برای مشاهده تحلیل‌ها ابتدا وارد شوید</p>
        </CardContent>
      </Card>
    );
  }

  const o = overview.data;
  const s = soilTrends.data;
  const n = ndviTrends.data;
  const p = performance.data;
  const c = carbon.data;

  const soilChartData = (s?.data ?? []).filter((d) => d.date).map((d) => ({ date: d.date, score: d.health_score }));
  const ndviChartData = (n?.data ?? []).filter((d) => d.date).map((d) => ({ date: d.date, ndvi: d.ndvi }));

  const distTotal = p ? p.total_soil_analyses : 0;
  const dist = p?.soil_health_distribution ?? { excellent: 0, good: 0, moderate: 0, poor: 0 };
  const distRows = [
    { key: "excellent", label: "عالی", value: dist.excellent, color: "bg-emerald-500" },
    { key: "good", label: "خوب", value: dist.good, color: "bg-lime-500" },
    { key: "moderate", label: "متوسط", value: dist.moderate, color: "bg-amber-500" },
    { key: "poor", label: "ضعیف", value: dist.poor, color: "bg-red-500" },
  ];

  return (
    <div className="space-y-4">
      {/* Overview stat cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[
          { icon: Sprout, label: "مزرعه‌ها", value: o?.farms_count ?? 0, sub: `${o?.total_area_hectares ?? 0} هکتار کل` },
          { icon: FlaskConical, label: "تحلیل خاک", value: o?.soil_analyses_count ?? 0 },
          { icon: Satellite, label: "تحلیل ماهواره‌ای", value: o?.satellite_analyses_count ?? 0 },
          { icon: Activity, label: "اجرای سناریو", value: o?.scenario_runs_count ?? 0 },
          { icon: Coins, label: "پروژه کربن", value: o?.carbon_projects_count ?? 0 },
          { icon: Leaf, label: "میانگین سلامت خاک", value: s?.average_health ?? 0, sub: TREND_LABELS[s?.trend ?? ""] ?? "" },
        ].map(({ icon: Icon, label, value, sub }) => (
          <Card key={label}>
            <CardContent className="flex items-center gap-4 p-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="text-xl font-bold text-foreground">{value}</p>
                {sub ? <p className="text-xs text-muted-foreground">{sub}</p> : null}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Trend charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">روند سلامت خاک</CardTitle>
            <CardDescription>میانگین امتیاز سلامت در طول زمان</CardDescription>
          </CardHeader>
          <CardContent>
            {soilChartData.length > 0 ? (
              <div className="h-56" dir="ltr">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={soilChartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.3} />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="score" stroke="#f97316" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="py-10 text-center text-sm text-muted-foreground">داده‌ای برای نمایش نیست.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">روند NDVI</CardTitle>
            <CardDescription>
              پوشش گیاهی از داده ماهواره‌ای
              {n ? <Badge variant="secondary" className="ms-2">{n.health_status}</Badge> : null}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {ndviChartData.length > 0 ? (
              <div className="h-56" dir="ltr">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={ndviChartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.3} />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="ndvi" stroke="#0ea5e9" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="py-10 text-center text-sm text-muted-foreground">داده‌ای برای نمایش نیست.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Distribution + Carbon */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">توزیع سلامت خاک</CardTitle>
            <CardDescription>بر اساس {distTotal} تحلیل ثبت‌شده</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {distTotal > 0 ? (
              distRows.map((r) => (
                <div key={r.key}>
                  <div className="mb-1 flex items-center justify-between text-sm">
                    <span className="text-foreground/80">{r.label}</span>
                    <span className="text-muted-foreground">{r.value}</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className={`h-full rounded-full ${r.color}`}
                      style={{ width: `${distTotal ? (r.value / distTotal) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="py-6 text-center text-sm text-muted-foreground">هنوز تحلیلی ثبت نشده است.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">خلاصه کربن</CardTitle>
            <CardDescription>پروژه‌های ترسیب کربن شما</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-xl border border-border bg-muted/20 p-3 text-center">
                <p className="text-lg font-bold text-foreground">{c?.total_projects ?? 0}</p>
                <p className="text-xs text-muted-foreground">پروژه</p>
              </div>
              <div className="rounded-xl border border-border bg-muted/20 p-3 text-center">
                <p className="text-lg font-bold text-foreground">{c?.total_area_hectares ?? 0}</p>
                <p className="text-xs text-muted-foreground">هکتار</p>
              </div>
              <div className="rounded-xl border border-border bg-muted/20 p-3 text-center">
                <p className="text-lg font-bold text-foreground">{c?.total_credits_issued ?? 0}</p>
                <p className="text-xs text-muted-foreground">اعتبار</p>
              </div>
            </div>
            {(c?.projects ?? []).length > 0 ? (
              <ul className="divide-y divide-border">
                {c!.projects.map((pr, i) => (
                  <li key={i} className="flex items-center justify-between gap-2 py-2 text-sm">
                    <span className="min-w-0 truncate font-semibold text-foreground">{pr.name}</span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {pr.credits_issued} اعتبار · {pr.area_hectares} هکتار
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="py-4 text-center text-sm text-muted-foreground">پروژه کربنی ثبت نشده است.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
