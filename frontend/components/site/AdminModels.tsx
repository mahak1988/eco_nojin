// AdminModels.tsx — list Ollama models + stop loaded one. Honest states.
"use client";

import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ShieldAlert, Cpu, PowerOff, RefreshCw } from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ModelInfo {
  name: string;
  size_bytes: number;
  family?: string | null;
  parameter_size?: string | null;
  quantization?: string | null;
  loaded: boolean;
}

interface ModelsResponse {
  configured: boolean;
  error?: string | null;
  models: ModelInfo[];
  loaded: string[];
  default_model: string;
}

export default function AdminModels() {
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

  const modelsQuery = useQuery({
    queryKey: ["admin-models", token],
    queryFn: async (): Promise<ModelsResponse> => {
      const res = await fetch(apiUrl("/api/v1/admin/models"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user?.role === "admin"),
  });

  const stopMutation = useMutation({
    mutationFn: async (name: string) => {
      const res = await fetch(apiUrl(`/api/v1/admin/models/${encodeURIComponent(name)}/stop`), {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `خطا (${res.status})`);
      }
      return res.json();
    },
    onSuccess: (data) => {
      toast.success(data.message ?? "مدل از حافظه خارج شد");
      queryClient.invalidateQueries({ queryKey: ["admin-models"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "خطا"),
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

  const data = modelsQuery.data;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <Cpu className="h-5 w-5 text-primary" />
          مدیریت مدل‌های هوش مصنوعی
        </CardTitle>
        <Button size="sm" variant="outline" onClick={() => modelsQuery.refetch()} disabled={modelsQuery.isFetching}>
          <RefreshCw className={`ml-1 h-4 w-4 ${modelsQuery.isFetching ? "animate-spin" : ""}`} />
          تازه‌سازی
        </Button>
      </CardHeader>
      <CardDescription className="px-6 pb-2">
        وضعیت زنده‌ی Ollama — مدل پیش‌فرض: {data?.default_model ?? "…"}
      </CardDescription>
      <CardContent>
        {modelsQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">در حال دریافت…</p>
        ) : data && !data.configured ? (
          <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
            سرور Ollama در دسترس نیست یا پیکربندی نشده است.
            <p className="mt-2 font-mono text-xs" dir="ltr">{data.error}</p>
            <p className="mt-2 text-xs">پس از راه‌اندازی Ollama، این صفحه به‌صورت زنده مدل‌ها را نشان می‌دهد.</p>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {(data?.models ?? []).map((m) => (
              <li key={m.name} className="flex flex-wrap items-center justify-between gap-2 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-foreground" dir="ltr">{m.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {m.family ?? "—"} {m.parameter_size ? `· ${m.parameter_size}` : ""}{" "}
                    {m.quantization ? `· ${m.quantization}` : ""} ·{" "}
                    {Math.round(m.size_bytes / 1e9 * 10) / 10} GB
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {m.loaded ? <Badge variant="success">بارگذاری‌شده</Badge> : <Badge variant="secondary">خالی</Badge>}
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!m.loaded || stopMutation.isPending}
                    onClick={() => stopMutation.mutate(m.name)}
                  >
                    <PowerOff className="ml-1 h-3.5 w-3.5" /> توقف
                  </Button>
                </div>
              </li>
            ))}
            {(data?.models ?? []).length === 0 && (
              <li className="py-3 text-sm text-muted-foreground">مدلی در Ollama نصب نشده است.</li>
            )}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
