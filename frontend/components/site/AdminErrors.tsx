"use client";

import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ShieldAlert, AlertTriangle, CheckCircle2, RefreshCw } from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ErrorRow {
  id: number;
  path: string;
  method: string;
  status: number;
  message?: string | null;
  acked: boolean;
  created_at?: string | null;
}

export default function AdminErrors() {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("auth_token") : null;
  const userJson = typeof window !== "undefined" ? window.localStorage.getItem("auth_user") : null;
  const user = useMemo(() => {
    try {
      return userJson ? (JSON.parse(userJson) as { role?: string }) : null;
    } catch {
      return null;
    }
  }, [userJson]);
  const queryClient = useQueryClient();

  const errorsQuery = useQuery({
    queryKey: ["admin-errors", token],
    queryFn: async (): Promise<ErrorRow[]> => {
      const res = await fetch(apiUrl("/api/v1/admin/errors"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user?.role === "admin"),
  });

  const ackMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(apiUrl(`/api/v1/admin/errors/${id}/ack`), {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    onSuccess: () => {
      toast.success("رسیدگی شد");
      queryClient.invalidateQueries({ queryKey: ["admin-errors"] });
    },
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

  const rows = errorsQuery.data ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-primary" />
          خطاهای ثبت‌شده
        </CardTitle>
        <Button size="sm" variant="outline" onClick={() => errorsQuery.refetch()} disabled={errorsQuery.isFetching}>
          <RefreshCw className={`ml-1 h-4 w-4 ${errorsQuery.isFetching ? "animate-spin" : ""}`} />
          تازه‌سازی
        </Button>
      </CardHeader>
      <CardDescription className="px-6 pb-2">
        خطاهای پیش‌بین‌نشده (500) توسط گیت‌وی به‌صورت خودکار ثبت می‌شوند.
      </CardDescription>
      <CardContent>
        {rows.length === 0 ? (
          <p className="text-sm text-muted-foreground">هنوز خطایی ثبت نشده است — عالی! 🎉</p>
        ) : (
          <ul className="divide-y divide-border">
            {rows.map((err) => (
              <li key={err.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-foreground">
                    {err.method} {err.path}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">
                    {err.message ?? "—"} — {err.created_at ? new Date(err.created_at).toLocaleString("fa-IR") : "—"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="destructive">500</Badge>
                  {err.acked ? (
                    <Badge variant="success">رسیدگی شد</Badge>
                  ) : (
                    <Button size="sm" variant="outline" onClick={() => ackMutation.mutate(err.id)}>
                      <CheckCircle2 className="ml-1 h-3.5 w-3.5" /> رسیدگی شد
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
