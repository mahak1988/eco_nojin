"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, RefreshCw, ShieldAlert, ShieldCheck } from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ChannelStatus {
  channel: string;
  status: string;
  detail: string;
}

interface HealthBody {
  status: string;
  channels: ChannelStatus[];
  checked_at: string;
}

const STATUS_META: Record<string, { label: string; variant: "success" | "warning" | "destructive" | "secondary" }> = {
  ok: { label: "سالم", variant: "success" },
  degraded: { label: "کاهش‌یافته", variant: "warning" },
  down: { label: "از کار افتاده", variant: "destructive" },
  not_configured: { label: "پیکربندی نشده", variant: "secondary" },
};

const CHANNEL_LABELS: Record<string, string> = {
  database: "پایگاه داده",
  ai_backend: "هوش مصنوعی (Ollama)",
  satellite: "ماهواره کوپرنیکوس",
  weather: "آب‌وهوا (NASA/ERA5)",
  telegram: "تلگرام",
  eitaa: "ایتا",
  bale: "بله",
  rubika: "روبیکا",
};

export default function AdminHealth() {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("auth_token") : null;
  const userJson = typeof window !== "undefined" ? window.localStorage.getItem("auth_user") : null;
  const user = useMemo(() => {
    try {
      return userJson ? (JSON.parse(userJson) as { role?: string }) : null;
    } catch {
      return null;
    }
  }, [userJson]);

  const healthQuery = useQuery({
    queryKey: ["admin-health", token],
    queryFn: async (): Promise<HealthBody> => {
      const res = await fetch(apiUrl("/api/v1/admin/health"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user?.role === "admin"),
  });

  if (user?.role !== "admin") {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
          <ShieldAlert className="h-10 w-10 text-muted-foreground" />
          <div className="space-y-1">
            <p className="font-semibold text-foreground">دسترسی ادمین لازم است</p>
            <p className="text-sm text-muted-foreground">
              این صفحه فقط برای نقش admin باز است. برای اولین ادمین:
              <code className="mx-1 rounded bg-muted px-1">UPDATE users SET role=&apos;admin&apos; WHERE email=&apos;you@example.com&apos;;</code>
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const channels = healthQuery.data?.channels ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            سلامت کانال‌های پلتفرم
          </CardTitle>
          <Button size="sm" variant="outline" onClick={() => healthQuery.refetch()} disabled={healthQuery.isFetching}>
            <RefreshCw className={`ml-1 h-4 w-4 ${healthQuery.isFetching ? "animate-spin" : ""}`} />
            بررسی مجدد
          </Button>
        </CardHeader>
        <CardDescription className="px-6 pb-2">
          {healthQuery.isError
            ? "خطا در خواندن وضعیت — نشست شما ممکن است منقضی شده باشد."
            : `آخرین بررسی: ${healthQuery.data?.checked_at ?? "—"}`}
        </CardDescription>
        <CardContent className="space-y-2">
          {healthQuery.isLoading && <p className="text-sm text-muted-foreground">در حال بررسی…</p>}
          {channels.map((c) => {
            const meta = STATUS_META[c.status] ?? STATUS_META.not_configured;
            return (
              <div key={c.channel} className="flex items-center justify-between gap-3 rounded-xl border border-border bg-muted/20 px-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-foreground">
                    {CHANNEL_LABELS[c.channel] ?? c.channel}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">{c.detail}</p>
                </div>
                <Badge variant={meta.variant} className="shrink-0">{meta.label}</Badge>
              </div>
            );
          })}
        </CardContent>
      </Card>
      <p className="flex items-center gap-2 rounded-xl bg-muted/30 p-3 text-xs text-muted-foreground">
        <ShieldCheck className="h-4 w-4 shrink-0 text-primary" />
        همه بررسی‌ها واقعی‌اند؛ کانال‌های پیکربندی‌نشده صادقانه گزارش می‌شوند، نه «سالم» نمایشی.
      </p>
    </div>
  );
}
