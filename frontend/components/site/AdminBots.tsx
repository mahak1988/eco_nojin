"use client";

import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ShieldAlert, Bot, Power } from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface BotInfo {
  key: string;
  label: string;
  kind: string;
  verified: boolean;
  configured: boolean;
  enabled: boolean;
}

export default function AdminBots() {
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

  const botsQuery = useQuery({
    queryKey: ["admin-bots", token],
    queryFn: async (): Promise<BotInfo[]> => {
      const res = await fetch(apiUrl("/api/v1/admin/bots"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user?.role === "admin"),
  });

  const toggleMutation = useMutation({
    mutationFn: async (key: string) => {
      const res = await fetch(apiUrl(`/api/v1/admin/bots/${key}/toggle`), {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ["admin-bots"] });
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

  const bots = botsQuery.data ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          مدیریت ربات‌ها
        </CardTitle>
        <CardDescription>
          وضعیت واقعی پیکربندی (توکن در env) + کلید فعال‌سازی که در تنظیمات ذخیره می‌شود.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2">
        {bots.map((b) => (
          <div key={b.key} className="flex items-center justify-between gap-3 rounded-xl border border-border bg-muted/20 px-4 py-3">
            <div>
              <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
                {b.label}
                {b.verified ? <Badge variant="success">تأییدشده</Badge> : <Badge variant="warning">در انتظار تأیید</Badge>}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {b.configured ? "توکن تنظیم شده" : "توکن تنظیم نشده"} — نوع: {b.kind}
              </p>
            </div>
            <Button
              size="sm"
              variant={b.enabled ? "default" : "outline"}
              onClick={() => toggleMutation.mutate(b.key)}
            >
              <Power className="ml-1 h-3.5 w-3.5" />
              {b.enabled ? "فعال" : "غیرفعال"}
            </Button>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
