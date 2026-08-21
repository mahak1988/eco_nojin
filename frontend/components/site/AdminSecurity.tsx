"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { ShieldAlert, ShieldCheck, KeyRound } from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface SecurityEvent {
  actor_email: string;
  target: string;
  detail?: string | null;
  created_at?: string | null;
}

export default function AdminSecurity() {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("auth_token") : null;
  const userJson = typeof window !== "undefined" ? window.localStorage.getItem("auth_user") : null;
  const user = useMemo(() => {
    try {
      return userJson ? (JSON.parse(userJson) as { role?: string }) : null;
    } catch {
      return null;
    }
  }, [userJson]);

  const security = useQuery({
    queryKey: ["admin-security", token],
    queryFn: async (): Promise<{ events: SecurityEvent[] }> => {
      const res = await fetch(apiUrl("/api/v1/admin/security"), {
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

  const events = security.data?.events ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <KeyRound className="h-5 w-5 text-primary" />
          امنیت — تاریخچه ورود
        </CardTitle>
        <CardDescription>
          آخرین ۵۰ تلاش ورود (موفق/ناموفق) که به‌صورت خودکار در لاگ ممیزی ثبت می‌شوند.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {security.isLoading ? (
          <p className="text-sm text-muted-foreground">در حال دریافت…</p>
        ) : events.length === 0 ? (
          <p className="text-sm text-muted-foreground">هنوز رویداد ورودی ثبت نشده است.</p>
        ) : (
          <ul className="divide-y divide-border">
            {events.map((e, i) => {
              const ok = (e.detail ?? "").startsWith("ok");
              return (
                <li key={i} className="flex flex-wrap items-center justify-between gap-2 py-3">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-foreground" dir="ltr">
                      {e.actor_email}
                    </p>
                    <p className="text-xs text-muted-foreground" dir="ltr">
                      {e.target} — {e.created_at ? new Date(e.created_at).toLocaleString("fa-IR") : "—"}
                    </p>
                  </div>
                  {ok ? (
                    <Badge variant="success">
                      <ShieldCheck className="ml-1 h-3 w-3" /> موفق
                    </Badge>
                  ) : (
                    <Badge variant="destructive">
                      <ShieldAlert className="ml-1 h-3 w-3" /> ناموفق
                    </Badge>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
