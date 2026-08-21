"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Leaf,
  MapPin,
  Satellite,
  ShieldCheck,
  Trophy,
  LogIn,
  ArrowLeft,
} from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { loadLearning, levelFor } from "@/lib/learning-store";

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

interface SatelliteHealth {
  status: string;
  module: string;
  data_source?: string;
}

export default function DashboardOverview() {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("auth_token") : null;
  const userJson = typeof window !== "undefined" ? window.localStorage.getItem("auth_user") : null;
  const user = useMemo(() => {
    try {
      return userJson ? (JSON.parse(userJson) as { full_name?: string; email?: string }) : null;
    } catch {
      return null;
    }
  }, [userJson]);

  const learning = useMemo(() => (typeof window !== "undefined" ? loadLearning() : null), []);
  const level = learning ? levelFor(learning.xp) : 0;

  const farmsQuery = useQuery({
    queryKey: ["farms", token],
    queryFn: async (): Promise<Farm[]> => {
      const res = await fetch(apiUrl("/api/v1/farms/"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token),
  });

  const healthQuery = useQuery({
    queryKey: ["sat-health"],
    queryFn: async (): Promise<SatelliteHealth> => {
      const res = await fetch(apiUrl("/api/v1/satellite/health"));
      if (!res.ok) throw new Error("health failed");
      return res.json();
    },
  });

  if (!token) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
          <LogIn className="h-10 w-10 text-muted-foreground" />
          <div className="space-y-1">
            <p className="font-semibold text-foreground">برای دیدن داده واقعی مزرعه‌ها وارد شوید</p>
            <p className="text-sm text-muted-foreground">
              این داشبورد به API واقعی پلتفرم متصل است؛ بدون ورود، داده‌ای نمایش نمی‌دهیم.
            </p>
          </div>
          <Button asChild>
            <Link href="/login">ورود / ثبت‌نام</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LayoutDashboard className="h-5 w-5 text-primary" />
            سلام {user?.full_name ?? user?.email ?? "کاربر"} 👋
          </CardTitle>
          <CardDescription>
            نمای کلی حساب شما — همه اعداد از API واقعی پلتفرم خوانده می‌شوند.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl bg-muted/40 p-4">
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <MapPin className="h-3.5 w-3.5" /> مزرعه‌های ثبت‌شده
            </p>
            <p className="mt-1 text-2xl font-bold text-foreground">
              {farmsQuery.isLoading ? "…" : farmsQuery.isError ? "—" : farmsQuery.data?.length ?? 0}
            </p>
          </div>
          <div className="rounded-xl bg-muted/40 p-4">
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Trophy className="h-3.5 w-3.5" /> سطح یادگیری
            </p>
            <p className="mt-1 text-2xl font-bold text-foreground">سطح {level}</p>
          </div>
          <div className="rounded-xl bg-muted/40 p-4">
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Satellite className="h-3.5 w-3.5" /> داده ماهواره‌ای
            </p>
            <p className="mt-1">
              <Badge variant={healthQuery.data?.data_source === "copernicus" ? "success" : "warning"}>
                {healthQuery.data?.data_source === "copernicus" ? "کوپرنیکوس واقعی" : "شبیه‌سازی (W-001)"}
              </Badge>
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Farms */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <Leaf className="h-4 w-4 text-primary" />
            مزرعه‌های شما
          </CardTitle>
          <Button asChild size="sm" variant="outline">
            <Link href="/dashboard/farm-detail">جزئیات مزرعه</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {farmsQuery.isLoading && <p className="text-sm text-muted-foreground">در حال خواندن از API…</p>}
          {farmsQuery.isError && (
            <p className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">
              خطا در خواندن مزرعه‌ها — نشست شما ممکن است منقضی شده باشد.
            </p>
          )}
          {farmsQuery.isSuccess && farmsQuery.data.length === 0 && (
            <p className="text-sm text-muted-foreground">
              هنوز مزرعه‌ای ثبت نکرده‌اید. از بخش «ثبت مزرعه» در داشبورد مزرعه شروع کنید.
            </p>
          )}
          {farmsQuery.isSuccess && farmsQuery.data.length > 0 && (
            <ul className="divide-y divide-border">
              {farmsQuery.data.map((farm) => (
                <li key={farm.id} className="flex items-center justify-between py-2.5">
                  <div>
                    <p className="text-sm font-semibold text-foreground">{farm.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {farm.area_hectares} هکتار — {farm.climate_zone ?? "—"} —{" "}
                      {farm.latitude.toFixed(4)}, {farm.longitude.toFixed(4)}
                    </p>
                  </div>
                  <Button asChild size="sm" variant="ghost">
                    <Link href={`/dashboard/farm-detail?farm_id=${farm.id}`}>
                      <ArrowLeft className="h-4 w-4 rtl:rotate-180" />
                    </Link>
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Honesty note */}
      <p className="flex items-center gap-2 rounded-xl bg-muted/30 p-3 text-xs text-muted-foreground">
        <ShieldCheck className="h-4 w-4 shrink-0 text-primary" />
        اصل صداقت: تا زمانی که اعتبارنامه کوپرنیکوس (CDSE) پیکربندی نشود، داده ماهواره‌ای برچسب
        «شبیه‌سازی» دارد و هرگز به‌عنوان داده واقعی نمایش داده نمی‌شود.
      </p>
    </div>
  );
}
