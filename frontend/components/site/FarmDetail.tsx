"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  MapPin,
  Leaf,
  Satellite,
  FlaskConical,
  RefreshCw,
  LogIn,
  Radar,
  CloudSun,
  BarChart3,
} from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Farm {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  area_hectares: number;
  soil_type?: string;
  climate_zone?: string;
  created_at?: string;
}

interface SoilAnalysis {
  id?: number;
  ph?: number;
  organic_matter?: number;
  nitrogen?: number;
  phosphorus?: number;
  potassium?: number;
  analyzed_at?: string;
}

interface SatelliteRow {
  id: number;
  farm_id: number;
  ndvi?: number | null;
  evi?: number | null;
  savi?: number | null;
  ndwi?: number | null;
  nbr?: number | null;
  satellite?: string | null;
  data_source?: string | null;
  scene_id?: string | null;
  cloud_cover?: number | null;
  analyzed_at: string;
}

interface AnalyzeResult {
  ndvi: number;
  evi: number;
  savi: number;
  recommendation: string;
  vegetation_health: string;
  data_source: string;
  scene_id?: string | null;
  cloud_cover?: number | null;
  sensed_at?: string | null;
}

interface WeatherSummary {
  status: string;
  source: string;
  days: number;
  summary?: {
    total_et0_mm: number;
    total_precipitation_mm: number;
    mean_temp_c: number;
    mean_et0_mm_day: number;
  };
}

interface SatelliteStats {
  analyses: number;
  ndvi_mean: number | null;
  ndvi_min: number | null;
  ndvi_max: number | null;
  ndvi_latest: number | null;
  real_data_count: number;
  engine: string;
}

function fmtDate(iso?: string) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("fa-IR");
  } catch {
    return iso;
  }
}

export default function FarmDetail() {
  const searchParams = useSearchParams();
  const farmId = searchParams.get("farm_id");
  const token = typeof window !== "undefined" ? window.localStorage.getItem("auth_token") : null;
  const queryClient = useQueryClient();

  const numId = farmId ? Number.parseInt(farmId, 10) : null;

  const farmQuery = useQuery({
    queryKey: ["farm", numId, token],
    queryFn: async (): Promise<Farm> => {
      const res = await fetch(apiUrl(`/api/v1/farms/${numId}`), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && numId),
  });

  const soilQuery = useQuery({
    queryKey: ["soil-history", numId],
    queryFn: async (): Promise<SoilAnalysis[]> => {
      const res = await fetch(apiUrl(`/api/v1/soil/history/${numId}`));
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(numId),
  });

  const satelliteQuery = useQuery({
    queryKey: ["sat-history", numId],
    queryFn: async (): Promise<SatelliteRow[]> => {
      const res = await fetch(apiUrl(`/api/v1/satellite/history/${numId}`));
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(numId),
  });

  const statsQuery = useQuery({
    queryKey: ["sat-stats", numId],
    queryFn: async (): Promise<SatelliteStats> => {
      const res = await fetch(apiUrl(`/api/v1/satellite/stats/${numId}`));
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(numId),
  });

  const weatherQuery = useQuery({
    queryKey: ["weather", numId, farmQuery.data?.latitude, farmQuery.data?.longitude],
    queryFn: async (): Promise<WeatherSummary> => {
      const farm = farmQuery.data!;
      const res = await fetch(
        apiUrl(`/api/v1/satellite/weather?lat=${farm.latitude}&lon=${farm.longitude}&days=7`)
      );
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(farmQuery.data),
    retry: 1,
  });

  const analyzeMutation = useMutation({
    mutationFn: async (): Promise<AnalyzeResult> => {
      const farm = farmQuery.data;
      if (!farm) throw new Error("مزرعه در دسترس نیست");
      const res = await fetch(apiUrl("/api/v1/satellite/analyze"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lat: farm.latitude, lon: farm.longitude, farm_id: farm.id }),
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    onSuccess: (data) => {
      toast.success(
        data.data_source === "copernicus"
          ? "تحلیل از داده واقعی کوپرنیکوس انجام شد"
          : "تحلیل ذخیره شد (منبع: شبیه‌سازی — W-001)"
      );
      queryClient.invalidateQueries({ queryKey: ["sat-history", numId] });
      queryClient.invalidateQueries({ queryKey: ["sat-stats", numId] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "خطا در تحلیل"),
  });

  const lastResult = useMemo(() => {
    if (analyzeMutation.data) return analyzeMutation.data;
    const rows = satelliteQuery.data ?? [];
    if (rows.length === 0) return null;
    const r = rows[0];
    return {
      ndvi: r.ndvi ?? 0,
      evi: r.evi ?? 0,
      savi: r.savi ?? 0,
      recommendation: "",
      vegetation_health: "—",
      data_source: r.data_source === "copernicus" ? "copernicus" : "simulated",
      scene_id: r.scene_id ?? null,
      cloud_cover: r.cloud_cover ?? null,
      sensed_at: r.analyzed_at ?? null,
    } satisfies AnalyzeResult;
  }, [analyzeMutation.data, satelliteQuery.data]);

  if (!token) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
          <LogIn className="h-10 w-10 text-muted-foreground" />
          <div className="space-y-1">
            <p className="font-semibold text-foreground">وارد شوید تا داده مزرعه را ببینید</p>
            <p className="text-sm text-muted-foreground">جزئیات مزرعه به حساب کاربری شما متصل است.</p>
          </div>
          <Button asChild>
            <Link href="/login">ورود / ثبت‌نام</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!numId) {
    return (
      <Card>
        <CardContent className="space-y-3 p-6">
          <p className="font-semibold text-foreground">مزرعه‌ای انتخاب نشده است</p>
          <p className="text-sm text-muted-foreground">
            آدرس را با شناسه مزرعه باز کنید: <code className="rounded bg-muted px-1">/dashboard/farm-detail?farm_id=1</code>
          </p>
          <Button asChild size="sm" variant="outline">
            <Link href="/dashboard/overview">بازگشت به نمای کلی</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  const farm = farmQuery.data;
  const soilRows = soilQuery.data ?? [];
  const satRows = satelliteQuery.data ?? [];
  const stats = statsQuery.data;
  const weather = weatherQuery.data;

  return (
    <div className="space-y-6">
      {/* Farm header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-primary" />
            {farm?.name ?? "مزرعه"}
          </CardTitle>
          <CardDescription>
            {farm
              ? `${farm.area_hectares} هکتار — ${farm.climate_zone ?? "منطقه نامشخص"} — خاک ${farm.soil_type ?? "نامشخص"} — مختصات ${farm.latitude.toFixed(4)}, ${farm.longitude.toFixed(4)}`
              : "در حال خواندن از API…"}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">
            <Leaf className="ml-1 h-3 w-3" /> {soilRows.length} تحلیل خاک
          </Badge>
          <Badge variant="secondary">
            <Satellite className="ml-1 h-3 w-3" /> {satRows.length} تحلیل ماهواره
          </Badge>
          <Button size="sm" onClick={() => analyzeMutation.mutate()} disabled={analyzeMutation.isPending}>
            <Radar className="ml-1 h-4 w-4" />
            {analyzeMutation.isPending ? "در حال تحلیل…" : "تحلیل زنده ماهواره"}
          </Button>
        </CardContent>
      </Card>

      {/* Real weather (NASA POWER — no credentials) */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <CloudSun className="h-4 w-4 text-primary" />
            آب‌وهوای واقعی ۷ روز اخیر
          </CardTitle>
          <Badge variant="success">NASA POWER</Badge>
        </CardHeader>
        <CardContent>
          {weatherQuery.isLoading && <p className="text-sm text-muted-foreground">در حال دریافت از NASA…</p>}
          {weatherQuery.isError && (
            <p className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">
              NASA POWER در دسترس نیست — بدون داده واقعی، عددی نمایش نمی‌دهیم.
            </p>
          )}
          {weather?.summary && (
            <div className="grid gap-3 sm:grid-cols-4">
              <div className="rounded-xl bg-muted/40 p-4 text-center">
                <p className="text-xs text-muted-foreground">دمای میانگین</p>
                <p className="text-2xl font-bold text-foreground">{weather.summary.mean_temp_c}°</p>
              </div>
              <div className="rounded-xl bg-muted/40 p-4 text-center">
                <p className="text-xs text-muted-foreground">بارش ۷ روز</p>
                <p className="text-2xl font-bold text-foreground">{weather.summary.total_precipitation_mm} mm</p>
              </div>
              <div className="rounded-xl bg-muted/40 p-4 text-center">
                <p className="text-xs text-muted-foreground">ET0 روزانه (Hargreaves)</p>
                <p className="text-2xl font-bold text-foreground">{weather.summary.mean_et0_mm_day} mm</p>
              </div>
              <div className="rounded-xl bg-muted/40 p-4 text-center">
                <p className="text-xs text-muted-foreground">مجموع ET0</p>
                <p className="text-2xl font-bold text-foreground">{weather.summary.total_et0_mm} mm</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Latest satellite result with provenance */}
      {lastResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Satellite className="h-4 w-4 text-primary" />
              آخرین نتیجه ماهواره
              <Badge variant={lastResult.data_source === "copernicus" ? "success" : "warning"}>
                {lastResult.data_source === "copernicus" ? "کوپرنیکوس واقعی" : "شبیه‌سازی (W-001)"}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-muted/40 p-4 text-center">
              <p className="text-xs text-muted-foreground">NDVI</p>
              <p className="text-2xl font-bold text-foreground">{lastResult.ndvi.toFixed(3)}</p>
              <p className="text-xs text-muted-foreground">
                {lastResult.vegetation_health === "good"
                  ? "پوشش گیاهی خوب"
                  : lastResult.vegetation_health === "moderate"
                    ? "پوشش متوسط"
                    : "پوشش ضعیف"}
              </p>
            </div>
            <div className="rounded-xl bg-muted/40 p-4 text-center">
              <p className="text-xs text-muted-foreground">EVI</p>
              <p className="text-2xl font-bold text-foreground">{lastResult.evi.toFixed(3)}</p>
            </div>
            <div className="rounded-xl bg-muted/40 p-4 text-center">
              <p className="text-xs text-muted-foreground">SAVI</p>
              <p className="text-2xl font-bold text-foreground">{lastResult.savi.toFixed(3)}</p>
            </div>
            {lastResult.recommendation && (
              <p className="sm:col-span-3 rounded-xl bg-primary/5 p-3 text-sm leading-7 text-foreground/90">
                {lastResult.recommendation}
              </p>
            )}
            {lastResult.data_source === "copernicus" && (
              <p className="sm:col-span-3 rounded-xl bg-muted/30 p-3 text-xs leading-6 text-muted-foreground">
                🛰️ صحنه: {lastResult.scene_id ?? "—"} — ابر: {lastResult.cloud_cover ?? "—"}٪ — تاریخ برداشت: {fmtDate(lastResult.sensed_at ?? undefined)}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* DuckDB stats */}
      {stats && stats.analyses > 0 && (
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="h-4 w-4 text-primary" />
              آمار NDVI (DuckDB)
            </CardTitle>
            <Badge variant="secondary">موتور: {stats.engine}</Badge>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-4">
            <div className="rounded-xl bg-muted/40 p-3 text-center">
              <p className="text-xs text-muted-foreground">تعداد تحلیل</p>
              <p className="text-xl font-bold text-foreground">{stats.analyses}</p>
            </div>
            <div className="rounded-xl bg-muted/40 p-3 text-center">
              <p className="text-xs text-muted-foreground">میانگین NDVI</p>
              <p className="text-xl font-bold text-foreground">{stats.ndvi_mean ?? "—"}</p>
            </div>
            <div className="rounded-xl bg-muted/40 p-3 text-center">
              <p className="text-xs text-muted-foreground">بازه NDVI</p>
              <p className="text-xl font-bold text-foreground">
                {stats.ndvi_min ?? "—"} تا {stats.ndvi_max ?? "—"}
              </p>
            </div>
            <div className="rounded-xl bg-muted/40 p-3 text-center">
              <p className="text-xs text-muted-foreground">داده واقعی</p>
              <p className="text-xl font-bold text-foreground">{stats.real_data_count} رکورد</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Soil history */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <FlaskConical className="h-4 w-4 text-primary" />
            تاریخچه تحلیل خاک
          </CardTitle>
          <Badge variant="secondary">{soilRows.length} رکورد</Badge>
        </CardHeader>
        <CardContent>
          {soilQuery.isLoading && <p className="text-sm text-muted-foreground">در حال خواندن…</p>}
          {soilQuery.isSuccess && soilRows.length === 0 && (
            <p className="text-sm text-muted-foreground">
              هنوز تحلیل خاکی ثبت نشده است — پس از ثبت اولین تحلیل، تاریخچه اینجا نمایش داده می‌شود.
            </p>
          )}
          {soilRows.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-right text-xs text-muted-foreground">
                    <th className="py-2 pe-3">تاریخ</th>
                    <th className="py-2 pe-3">pH</th>
                    <th className="py-2 pe-3">ماده آلی</th>
                    <th className="py-2 pe-3">نیتروژن</th>
                    <th className="py-2 pe-3">فسفر</th>
                    <th className="py-2">پتاسیم</th>
                  </tr>
                </thead>
                <tbody>
                  {soilRows.map((row, i) => (
                    <tr key={row.id ?? i} className="border-b border-border/50">
                      <td className="py-2 pe-3">{fmtDate(row.analyzed_at)}</td>
                      <td className="py-2 pe-3">{row.ph ?? "—"}</td>
                      <td className="py-2 pe-3">{row.organic_matter ?? "—"}</td>
                      <td className="py-2 pe-3">{row.nitrogen ?? "—"}</td>
                      <td className="py-2 pe-3">{row.phosphorus ?? "—"}</td>
                      <td className="py-2">{row.potassium ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Satellite history */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <Satellite className="h-4 w-4 text-primary" />
            تاریخچه تحلیل ماهواره
          </CardTitle>
          <Badge variant="secondary">{satRows.length} رکورد</Badge>
        </CardHeader>
        <CardContent>
          {satRows.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              هنوز تحلیلی ثبت نشده — دکمه «تحلیل زنده ماهواره» را بزنید تا اولین رکورد ذخیره شود.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {satRows.map((row) => (
                <li key={row.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
                  <div className="text-sm">
                    <span className="font-semibold text-foreground">{fmtDate(row.analyzed_at)}</span>
                    <span className="ms-2 text-xs text-muted-foreground">
                      منبع: {row.data_source === "copernicus" ? "کوپرنیکوس (واقعی)" : "شبیه‌سازی"}
                    </span>
                  </div>
                  <div className="flex gap-3 text-xs text-muted-foreground">
                    <span>NDVI: <b className="text-foreground">{row.ndvi?.toFixed(3) ?? "—"}</b></span>
                    <span>EVI: <b className="text-foreground">{row.evi?.toFixed(3) ?? "—"}</b></span>
                    <span>SAVI: <b className="text-foreground">{row.savi?.toFixed(3) ?? "—"}</b></span>
                  </div>
                </li>
              ))}
            </ul>
          )}
          {satRows.length > 0 && (
            <Button size="sm" variant="ghost" className="mt-2" onClick={() => satelliteQuery.refetch()}>
              <RefreshCw className="ml-1 h-3.5 w-3.5" /> تازه‌سازی
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
