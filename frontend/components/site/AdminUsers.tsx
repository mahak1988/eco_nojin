"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ShieldAlert, Users, Ban, CheckCircle2 } from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_email_verified: boolean;
  language?: string | null;
  created_at?: string | null;
}

const ROLE_LABELS: Record<string, string> = {
  admin: "مدیر",
  farmer: "کشاورز",
  advisor: "کارشناس",
  researcher: "پژوهشگر",
  organization: "سازمان",
  tourist: "گردشگر",
  regular: "عادی",
};

export default function AdminUsers() {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("auth_token") : null;
  const userJson = typeof window !== "undefined" ? window.localStorage.getItem("auth_user") : null;
  const user = useMemo(() => {
    try {
      return userJson ? (JSON.parse(userJson) as { role?: string; id?: number }) : null;
    } catch {
      return null;
    }
  }, [userJson]);
  const queryClient = useQueryClient();

  const usersQuery = useQuery({
    queryKey: ["admin-users", token],
    queryFn: async (): Promise<AdminUser[]> => {
      const res = await fetch(apiUrl("/api/v1/admin/users"), {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user?.role === "admin"),
  });

  const setActiveMutation = useMutation({
    mutationFn: async ({ userId, active }: { userId: number; active: boolean }) => {
      const res = await fetch(apiUrl(`/api/v1/admin/users/${userId}/${active ? "unblock" : "block"}`), {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    onSuccess: (data, vars) => {
      toast.success(vars.active ? "کاربر فعال شد" : "کاربر مسدود شد");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "خطا در تغییر وضعیت"),
  });

  if (user?.role !== "admin") {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
          <ShieldAlert className="h-10 w-10 text-muted-foreground" />
          <p className="font-semibold text-foreground">دسترسی ادمین لازم است</p>
          <p className="text-sm text-muted-foreground">
            مدیریت کاربران فقط با نقش admin در دسترس است.
          </p>
        </CardContent>
      </Card>
    );
  }

  const rows = usersQuery.data ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5 text-primary" />
          مدیریت کاربران
        </CardTitle>
        <Badge variant="secondary">{rows.length} کاربر</Badge>
      </CardHeader>
      <CardDescription className="px-6 pb-2">
        مسدودسازی/فعال‌سازی واقعی روی پایگاه داده اعمال می‌شود و در لاگ ممیزی ثبت می‌گردد.
      </CardDescription>
      <CardContent>
        {usersQuery.isLoading && <p className="text-sm text-muted-foreground">در حال خواندن…</p>}
        {usersQuery.isError && (
          <p className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">
            خطا در خواندن کاربران — نشست منقضی شده؟
          </p>
        )}
        {rows.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-right text-xs text-muted-foreground">
                  <th className="py-2 pe-3">نام</th>
                  <th className="py-2 pe-3">ایمیل</th>
                  <th className="py-2 pe-3">نقش</th>
                  <th className="py-2 pe-3">وضعیت</th>
                  <th className="py-2">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((u) => (
                  <tr key={u.id} className="border-b border-border/50">
                    <td className="py-2 pe-3 font-semibold text-foreground">{u.full_name}</td>
                    <td className="py-2 pe-3 text-muted-foreground">{u.email}</td>
                    <td className="py-2 pe-3">
                      <Badge variant={u.role === "admin" ? "success" : "secondary"}>
                        {ROLE_LABELS[u.role] ?? u.role}
                      </Badge>
                    </td>
                    <td className="py-2 pe-3">
                      <Badge variant={u.is_active ? "success" : "destructive"}>
                        {u.is_active ? "فعال" : "مسدود"}
                      </Badge>
                    </td>
                    <td className="py-2">
                      {u.id === user?.id ? (
                        <span className="text-xs text-muted-foreground">—</span>
                      ) : u.is_active ? (
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-destructive"
                          disabled={setActiveMutation.isPending}
                          onClick={() => setActiveMutation.mutate({ userId: u.id, active: false })}
                        >
                          <Ban className="ml-1 h-3.5 w-3.5" /> مسدود
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={setActiveMutation.isPending}
                          onClick={() => setActiveMutation.mutate({ userId: u.id, active: true })}
                        >
                          <CheckCircle2 className="ml-1 h-3.5 w-3.5" /> فعال‌سازی
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
