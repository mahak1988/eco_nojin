"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ShieldAlert, Settings } from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

interface SettingRow {
  key: string;
  value: string;
  description?: string | null;
  updated_at?: string | null;
}

const SETTING_LABELS: Record<string, string> = {
  site_announcement: "پیام سراسری سایت",
  alerts_ndvi_enabled: "فعال‌سازی هشدارهای NDVI",
  rag_available: "در دسترس بودن دانشنامه",
  default_language: "زبان پیش‌فرض",
  content_auto_publish_bot: "انتشار خودکار به ربات‌ها",
  content_publish_channel: "شناسه کانال ربات",
};

export default function AdminSettings() {
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
  const [edits, setEdits] = useState<Record<string, string>>({});

  const settingsQuery = useQuery({
    queryKey: ["admin-settings", token],
    queryFn: async (): Promise<SettingRow[]> => {
      const res = await fetch(apiUrl("/api/v1/admin/settings"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user?.role === "admin"),
  });

  const saveMutation = useMutation({
    mutationFn: async ({ key, value }: { key: string; value: string }) => {
      const res = await fetch(apiUrl(`/api/v1/admin/settings/${key}`), {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ value }),
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    onSuccess: (data) => {
      toast.success(`«${SETTING_LABELS[data.key] ?? data.key}» ذخیره شد`);
      setEdits((prev) => ({ ...prev, [data.key]: "" }));
      queryClient.invalidateQueries({ queryKey: ["admin-settings"] });
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

  const rows = settingsQuery.data ?? [];
  const knownKeys = [
    "site_announcement",
    "alerts_ndvi_enabled",
    "rag_available",
    "default_language",
    "content_auto_publish_bot",
    "content_publish_channel",
  ];
  const present = new Set(rows.map((r) => r.key));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5 text-primary" />
          تنظیمات سراسری
        </CardTitle>
        <CardDescription>کلیدهای شناخته‌شده — مقادیر در پایگاه داده ذخیره و ممیزی می‌شوند.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {knownKeys.map((key) => {
          const row = rows.find((r) => r.key === key);
          const value = edits[key] ?? row?.value ?? "";
          return (
            <div key={key} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-muted/20 px-4 py-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-foreground">{SETTING_LABELS[key] ?? key}</p>
                <p className="text-xs text-muted-foreground">{row?.description ?? "—"}</p>
                {!present.has(key) && <Badge variant="secondary" className="mt-1">پیش‌فرض</Badge>}
              </div>
              <div className="flex items-center gap-2">
                <Input
                  dir="rtl"
                  className="w-56"
                  value={value}
                  placeholder={row?.value ?? ""}
                  onChange={(e) => setEdits((prev) => ({ ...prev, [key]: e.target.value }))}
                />
                <Button
                  size="sm"
                  variant={edits[key] !== undefined ? "default" : "outline"}
                  disabled={saveMutation.isPending || !edits[key] || edits[key] === row?.value}
                  onClick={() => saveMutation.mutate({ key, value: edits[key] })}
                >
                  ذخیره
                </Button>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
