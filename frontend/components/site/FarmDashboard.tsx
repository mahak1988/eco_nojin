"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { LogIn, MapPin, Ruler, Sprout } from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface Farm {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  area_hectares: number;
  soil_type?: string | null;
}

function readToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

export default function FarmDashboard() {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", area: "", lat: "", lon: "", soil: "" });

  useEffect(() => {
    setToken(readToken());
  }, []);

  const farmsQuery = useQuery({
    queryKey: ["my-farms", token],
    enabled: Boolean(token),
    queryFn: async (): Promise<Farm[]> => {
      const res = await fetch(apiUrl("/api/v1/farms/"), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        localStorage.removeItem("auth_token");
        setToken(null);
        throw new Error("نشست شما منقضی شده است؛ دوباره وارد شوید.");
      }
      if (!res.ok) throw new Error(`خطا در دریافت مزرعه‌ها (${res.status})`);
      return res.json();
    },
  });

  const createFarm = useMutation({
    mutationFn: async (): Promise<void> => {
      const body = {
        name: form.name,
        area_hectares: parseFloat(form.area),
        latitude: parseFloat(form.lat),
        longitude: parseFloat(form.lon),
        soil_type: form.soil || null,
      };
      const res = await fetch(apiUrl("/api/v1/farms/"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`ثبت ناموفق (${res.status})`);
    },
    onSuccess: () => {
      toast.success("مزرعه با موفقیت ثبت شد");
      setForm({ name: "", area: "", lat: "", lon: "", soil: "" });
      queryClient.invalidateQueries({ queryKey: ["my-farms"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "خطا در ثبت"),
  });

  if (!token) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
          <LogIn className="h-8 w-8 text-primary" />
          <p className="font-semibold text-foreground">برای مدیریت مزرعه‌های خود وارد شوید</p>
          <p className="text-sm text-muted-foreground">
            مزرعه‌های ثبت‌شده از ربات یا وب، اینجا نمایش داده می‌شوند.
          </p>
          <div className="flex gap-2">
            <Button asChild>
              <a href="/login">ورود</a>
            </Button>
            <Button variant="outline" asChild>
              <a href="/register">ثبت‌نام</a>
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sprout className="h-5 w-5 text-primary" />
            مزرعه‌های من
          </CardTitle>
        </CardHeader>
        <CardContent>
          {farmsQuery.isPending && <p className="text-sm text-muted-foreground">در حال بارگذاری…</p>}
          {farmsQuery.isError && (
            <p className="text-sm text-destructive">
              {farmsQuery.error instanceof Error ? farmsQuery.error.message : "خطا در بارگذاری"}
            </p>
          )}
          {farmsQuery.data && farmsQuery.data.length === 0 && (
            <p className="text-sm text-muted-foreground">هنوز مزرعه‌ای ثبت نکرده‌اید.</p>
          )}
          {farmsQuery.data && farmsQuery.data.length > 0 && (
            <ul className="space-y-2">
              {farmsQuery.data.map((f) => (
                <li
                  key={f.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border p-3"
                >
                  <span className="font-semibold text-foreground">{f.name}</span>
                  <span className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Ruler className="h-3.5 w-3.5" /> {f.area_hectares} هکتار
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5" /> {f.latitude.toFixed(4)}, {f.longitude.toFixed(4)}
                    </span>
                    {f.soil_type && <Badge variant="secondary">{f.soil_type}</Badge>}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">ثبت مزرعه جدید</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1.5 text-sm">
              نام مزرعه
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="مثلاً مزرعه قنات" />
            </label>
            <label className="space-y-1.5 text-sm">
              مساحت (هکتار)
              <Input inputMode="decimal" dir="ltr" value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} placeholder="5.5" />
            </label>
            <label className="space-y-1.5 text-sm">
              عرض جغرافیایی
              <Input inputMode="decimal" dir="ltr" value={form.lat} onChange={(e) => setForm({ ...form, lat: e.target.value })} placeholder="35.6892" />
            </label>
            <label className="space-y-1.5 text-sm">
              طول جغرافیایی
              <Input inputMode="decimal" dir="ltr" value={form.lon} onChange={(e) => setForm({ ...form, lon: e.target.value })} placeholder="51.3890" />
            </label>
            <label className="space-y-1.5 text-sm sm:col-span-2">
              نوع خاک (اختیاری)
              <Input value={form.soil} onChange={(e) => setForm({ ...form, soil: e.target.value })} placeholder="لومی، شنی، رسی…" />
            </label>
          </div>
          <Button
            className="mt-4"
            onClick={() => createFarm.mutate()}
            disabled={createFarm.isPending || !form.name || !form.area || !form.lat || !form.lon}
          >
            {createFarm.isPending ? "در حال ثبت…" : "ثبت مزرعه"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
