"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  Clock,
  FileText,
  ShieldAlert,
  ShieldCheck,
  Users,
} from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface OverviewData {
  uptime_seconds: number;
  counts: {
    users: number;
    farms: number;
    audit_entries: number;
    errors_total: number;
    errors_open: number;
    content_total: number;
    content_published: number;
  };
  recent_audit: { actor_email: string; action: string; target: string; detail?: string | null; created_at?: string | null }[];
  recent_errors: { id: number; path: string; method: string; status: number; acked: boolean; created_at?: string | null }[];
}

function fmtUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h} ساعت و ${m} دقیقه`;
  return `${m} دقیقه`;
}

export default function AdminOverview() {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("auth_token") : null;
  const userJson = typeof window !== "undefined" ? window.localStorage.getItem("auth_user") : null;
  const user = useMemo(() => {
    try {
      return userJson ? (JSON.parse(userJson) as { role?: string }) : null;
    } catch {
      return null;
    }
  }, [userJson]);

  const overview = useQuery({
    queryKey: ["admin-overview", token],
    queryFn: async (): Promise<OverviewData> => {
      const res = await fetch(apiUrl("/api/v1/admin/overview"), {
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
          <p className="font-semibold text-foreground">دسترسی ادمین لازم است</p>
        </CardContent>
      </Card>
    );
  }

  const d = overview.data;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            نمای کلی پلتفرم
          </CardTitle>
          <CardDescription>متریکهای واقعی و زنده — بدون عدد ساختگی.</CardDescription>
        </CardHeader>
        <CardContent>
          {overview.isLoading ? (
            <p className="text-sm text-muted-foreground">در حال دریافت…</p>
          ) : d ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { icon: Clock, label: "آپتایم", value: fmtUptime(d.uptime_seconds) },
                { icon: Users, label: "کاربران", value: String(d.counts.users) },
                { icon: FileText, label: "محتوا (منتشرشده)", value: `${d.counts.content_published} / ${d.counts.content_total}` },
                { icon: ShieldCheck, label: "رویدادهای ممیزی", value: String(d.counts.audit_entries) },
                { icon: AlertTriangle, label: "خطاهای باز", value: String(d.counts.errors_open), danger: d.counts.errors_open > 0 },
                { icon: Activity, label: "مزارع", value: String(d.counts.farms) },
              ].map(({ icon: Icon, label, value, danger }) => (
                <div key={label} className="rounded-xl border border-border bg-muted/20 px-4 py-3">
                  <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Icon className={`h-3.5 w-3.5 ${danger ? "text-destructive" : ""}`} />
                    {label}
                  </p>
                  <p className={`mt-1 text-xl font-bold ${danger ? "text-destructive" : "text-foreground"}`}>{value}</p>
                </div>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">آخرین فعالیت‌های ممیزی</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border">
              {(d?.recent_audit ?? []).map((a, i) => (
                <li key={i} className="flex items-center justify-between gap-2 py-2 text-sm">
                  <span className="min-w-0 truncate text-foreground" dir="ltr">
                    {a.actor_email}
                  </span>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {a.action} — {a.detail ?? a.target}
                  </span>
                </li>
              ))}
              {(d?.recent_audit ?? []).length === 0 && (
                <li className="py-2 text-sm text-muted-foreground">هنوز فعالیتی ثبت نشده.</li>
              )}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">آخرین خطاها</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border">
              {(d?.recent_errors ?? []).map((e) => (
                <li key={e.id} className="flex items-center justify-between gap-2 py-2 text-sm">
                  <span className="min-w-0 truncate text-foreground" dir="ltr">
                    {e.method} {e.path}
                  </span>
                  {e.acked ? (
                    <Badge variant="secondary">رسیدگی شد</Badge>
                  ) : (
                    <Badge variant="destructive">باز</Badge>
                  )}
                </li>
              ))}
              {(d?.recent_errors ?? []).length === 0 && (
                <li className="py-2 text-sm text-muted-foreground">خطایی ثبت نشده — عالی! 🎉</li>
              )}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
