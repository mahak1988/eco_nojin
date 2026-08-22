"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Sprout, Trash2 } from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface Farm {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  elevation_m: number | null;
  area_hectares: number;
  soil_type: string | null;
  climate_zone: string | null;
}

const EMPTY_FORM = {
  name: "",
  latitude: "",
  longitude: "",
  area_hectares: "",
  elevation_m: "",
  soil_type: "",
  climate_zone: "",
};

export default function AdminFarms() {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("auth_token") : null;
  const userJson = typeof window !== "undefined" ? window.localStorage.getItem("auth_user") : null;
  const user = useMemo(() => {
    try {
      return userJson ? (JSON.parse(userJson) as { id?: number }) : null;
    } catch {
      return null;
    }
  }, [userJson]);
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  const farmsQuery = useQuery({
    queryKey: ["farms", token],
    queryFn: async (): Promise<Farm[]> => {
      const res = await fetch(apiUrl("/api/v1/farms/"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user),
  });

  const createMutation = useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      const res = await fetch(apiUrl("/api/v1/farms/"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    onSuccess: () => {
      toast.success("مزرعه با موفقیت ایجاد شد");
      setOpen(false);
      setForm(EMPTY_FORM);
      queryClient.invalidateQueries({ queryKey: ["farms"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "خطا در ایجاد مزرعه"),
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(apiUrl(`/api/v1/farms/${id}`), {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    onSuccess: () => {
      toast.success("مزرعه حذف شد");
      queryClient.invalidateQueries({ queryKey: ["farms"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "خطا در حذف مزرعه"),
  });

  if (!token) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-3 p-10 text-center">
          <Sprout className="h-10 w-10 text-muted-foreground" />
          <p className="font-semibold text-foreground">برای مدیریت مزرعه‌ها ابتدا وارد شوید</p>
        </CardContent>
      </Card>
    );
  }

  const rows = farmsQuery.data ?? [];

  function update(field: keyof typeof EMPTY_FORM, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function submit() {
    const lat = parseFloat(form.latitude);
    const lng = parseFloat(form.longitude);
    const area = parseFloat(form.area_hectares);
    if (!form.name.trim() || Number.isNaN(lat) || Number.isNaN(lng) || Number.isNaN(area)) {
      toast.error("نام، عرض جغرافیایی، طول جغرافیایی و مساحت الزامی است");
      return;
    }
    createMutation.mutate({
      name: form.name.trim(),
      latitude: lat,
      longitude: lng,
      area_hectares: area,
      elevation_m: form.elevation_m ? parseFloat(form.elevation_m) : null,
      soil_type: form.soil_type.trim() || null,
      climate_zone: form.climate_zone.trim() || null,
    });
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <Sprout className="h-5 w-5 text-primary" />
          مدیریت مزرعه‌ها
        </CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{rows.length} مزرعه</Badge>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="ml-1 h-4 w-4" /> افزودن مزرعه
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle>افزودن مزرعه جدید</DialogTitle>
                <DialogDescription>مشخصات پایه مزرعه را وارد کنید.</DialogDescription>
              </DialogHeader>
              <div className="grid gap-3 py-2">
                <div className="grid gap-1.5">
                  <Label htmlFor="farm-name">نام مزرعه *</Label>
                  <Input
                    id="farm-name"
                    value={form.name}
                    onChange={(e) => update("name", e.target.value)}
                    placeholder="مثلاً مزرعه نارون"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-1.5">
                    <Label htmlFor="farm-lat">عرض جغرافیایی *</Label>
                    <Input
                      id="farm-lat"
                      inputMode="decimal"
                      value={form.latitude}
                      onChange={(e) => update("latitude", e.target.value)}
                      placeholder="35.6892"
                      dir="ltr"
                    />
                  </div>
                  <div className="grid gap-1.5">
                    <Label htmlFor="farm-lng">طول جغرافیایی *</Label>
                    <Input
                      id="farm-lng"
                      inputMode="decimal"
                      value={form.longitude}
                      onChange={(e) => update("longitude", e.target.value)}
                      placeholder="51.3890"
                      dir="ltr"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-1.5">
                    <Label htmlFor="farm-area">مساحت (هکتار) *</Label>
                    <Input
                      id="farm-area"
                      inputMode="decimal"
                      value={form.area_hectares}
                      onChange={(e) => update("area_hectares", e.target.value)}
                      placeholder="10"
                      dir="ltr"
                    />
                  </div>
                  <div className="grid gap-1.5">
                    <Label htmlFor="farm-elev">ارتفاع از سطح دریا (متر)</Label>
                    <Input
                      id="farm-elev"
                      inputMode="decimal"
                      value={form.elevation_m}
                      onChange={(e) => update("elevation_m", e.target.value)}
                      placeholder="1200"
                      dir="ltr"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-1.5">
                    <Label htmlFor="farm-soil">نوع خاک</Label>
                    <Input
                      id="farm-soil"
                      value={form.soil_type}
                      onChange={(e) => update("soil_type", e.target.value)}
                      placeholder="رسی / شنی / ..."
                    />
                  </div>
                  <div className="grid gap-1.5">
                    <Label htmlFor="farm-climate">اقلیم</Label>
                    <Input
                      id="farm-climate"
                      value={form.climate_zone}
                      onChange={(e) => update("climate_zone", e.target.value)}
                      placeholder="نیمه‌خشک / ..."
                    />
                  </div>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <DialogClose asChild>
                  <Button variant="outline">انصراف</Button>
                </DialogClose>
                <Button onClick={submit} disabled={createMutation.isPending}>
                  {createMutation.isPending ? "در حال ثبت..." : "ثبت مزرعه"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardDescription className="px-6 pb-2">
        فهرست مزرعه‌های ثبت‌شده به همراه موقعیت و مساحت آن‌ها.
      </CardDescription>
      <CardContent>
        {farmsQuery.isLoading && <p className="text-sm text-muted-foreground">در حال بارگذاری...</p>}
        {farmsQuery.isError && (
          <p className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">
            خطا در دریافت مزرعه‌ها.
          </p>
        )}
        {rows.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-right text-xs text-muted-foreground">
                  <th className="py-2 pe-3">نام</th>
                  <th className="py-2 pe-3">مختصات</th>
                  <th className="py-2 pe-3">مساحت</th>
                  <th className="py-2 pe-3">نوع خاک</th>
                  <th className="py-2 pe-3">اقلیم</th>
                  <th className="py-2">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((f) => (
                  <tr key={f.id} className="border-b border-border/50">
                    <td className="py-2 pe-3 font-semibold text-foreground">{f.name}</td>
                    <td className="py-2 pe-3 text-muted-foreground" dir="ltr">
                      {f.latitude.toFixed(4)}، {f.longitude.toFixed(4)}
                    </td>
                    <td className="py-2 pe-3">{f.area_hectares} هکتار</td>
                    <td className="py-2 pe-3 text-muted-foreground">{f.soil_type ?? "—"}</td>
                    <td className="py-2 pe-3 text-muted-foreground">{f.climate_zone ?? "—"}</td>
                    <td className="py-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-destructive"
                        disabled={deleteMutation.isPending}
                        onClick={() => deleteMutation.mutate(f.id)}
                      >
                        <Trash2 className="ml-1 h-3.5 w-3.5" /> حذف
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!farmsQuery.isLoading && rows.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">هنوز مزرعه‌ای ثبت نشده است.</p>
        )}
      </CardContent>
    </Card>
  );
}
