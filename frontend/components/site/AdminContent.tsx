"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Bot,
  FileText,
  Languages,
  Plus,
  Send,
  ShieldAlert,
  CalendarClock,
  History,
  Sparkles,
} from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import MarkdownView from "@/components/site/MarkdownView";

interface ContentItem {
  id: number;
  title: string;
  body: string;
  category: string;
  language: string;
  status: string;
  source?: string | null;
  updated_at?: string | null;
  generated_by_ai?: boolean;
  rag_synced?: boolean;
}

interface VersionRow {
  version: number;
  title: string;
  body: string;
  created_at?: string | null;
}

interface TranslationRow {
  language: string;
  title: string;
  body: string;
  source: string;
  created_at?: string | null;
}

const STATUS_BADGE: Record<string, "secondary" | "success" | "warning"> = {
  draft: "secondary",
  published: "success",
  archived: "warning",
};

const CATEGORY_LABELS: Record<string, string> = {
  agriculture: "کشاورزی",
  water: "آب",
  soil: "خاک",
  carbon: "کربن",
  climate: "اقلیم",
  general: "عمومی",
};

const LANGUAGES: [string, string][] = [
  ["fa", "فارسی"], ["en", "English"], ["ar", "العربية"], ["tr", "Türkçe"],
  ["ru", "Русский"], ["zh", "中文"], ["es", "Español"], ["fr", "Français"],
  ["de", "Deutsch"], ["ur", "اردو"], ["az", "Azərbaycanca"], ["ku", "Kurdî"],
  ["hi", "हिन्दी"], ["ps", "پښتو"],
];

export default function AdminContent() {
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

  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [category, setCategory] = useState("general");
  const [mode, setMode] = useState<"edit" | "preview">("edit");
  const [activeId, setActiveId] = useState<number | null>(null);
  const [lang, setLang] = useState("en");
  const [topic, setTopic] = useState("");
  const [scheduleAt, setScheduleAt] = useState("");

  const headers = useMemo(
    () => ({ ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
    [token],
  );

  const listQuery = useQuery({
    queryKey: ["admin-content", token],
    queryFn: async (): Promise<ContentItem[]> => {
      const res = await fetch(apiUrl("/api/v1/admin/content"), { headers });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(token && user?.role === "admin"),
  });

  const versionsQuery = useQuery({
    queryKey: ["admin-content-versions", activeId, token],
    queryFn: async (): Promise<VersionRow[]> => {
      const res = await fetch(apiUrl(`/api/v1/admin/content/${activeId}/versions`), { headers });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(activeId && token && user?.role === "admin"),
  });

  const translationsQuery = useQuery({
    queryKey: ["admin-content-translations", activeId, token],
    queryFn: async (): Promise<TranslationRow[]> => {
      const res = await fetch(apiUrl(`/api/v1/admin/content/${activeId}/translations`), { headers });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    enabled: Boolean(activeId && token && user?.role === "admin"),
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(apiUrl("/api/v1/admin/content"), {
        method: "POST",
        headers: { "Content-Type": "application/json", ...headers },
        body: JSON.stringify({ title, body, category, language: "fa" }),
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    onSuccess: () => {
      toast.success("پیش‌نویس ساخته شد (نسخه ۱ ثبت شد)");
      setTitle("");
      setBody("");
      queryClient.invalidateQueries({ queryKey: ["admin-content"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "خطا"),
  });

  const publishMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(apiUrl(`/api/v1/admin/content/${id}/publish`), {
        method: "POST",
        headers,
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ["admin-content"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "خطا"),
  });

  const aiDraftMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(
        apiUrl(`/api/v1/admin/content/generate-draft?topic=${encodeURIComponent(topic)}&category=${encodeURIComponent(category)}`),
        { method: "POST", headers },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `خطا (${res.status})`);
      }
      return res.json();
    },
    onSuccess: () => {
      toast.success("پیش‌نویس AI ساخته شد");
      setTopic("");
      queryClient.invalidateQueries({ queryKey: ["admin-content"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "خطا"),
  });

  const scheduleMutation = useMutation({
    mutationFn: async ({ id, at }: { id: number; at: string }) => {
      const res = await fetch(
        apiUrl(`/api/v1/admin/content/${id}/schedule?at=${encodeURIComponent(at)}`),
        { method: "POST", headers },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `خطا (${res.status})`);
      }
      return res.json();
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ["admin-content"] });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "خطا"),
  });

  const cancelScheduleMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(apiUrl(`/api/v1/admin/content/${id}/cancel-schedule`), {
        method: "POST",
        headers,
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ["admin-content"] });
    },
  });

  const translateMutation = useMutation({
    mutationFn: async ({ id, language }: { id: number; language: string }) => {
      const res = await fetch(
        apiUrl(`/api/v1/admin/content/${id}/translate?language=${encodeURIComponent(language)}`),
        { method: "POST", headers },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `خطا (${res.status})`);
      }
      return res.json();
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ["admin-content-translations"] });
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

  const rows = listQuery.data ?? [];
  const active = rows.find((r) => r.id === activeId) ?? null;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            تولید محتوا (فاز ۶)
          </CardTitle>
          <Badge variant="secondary">{rows.length} مورد</Badge>
        </CardHeader>
        <CardDescription className="px-6 pb-2">
          ویرایشگر Markdown با پیش‌نمایش زنده، تاریخچه نسخه‌ها، ترجمه AI به ۱۴ زبان و همگام‌سازی RAG هنگام انتشار.
        </CardDescription>
        <CardContent className="space-y-3">
          <Input dir="rtl" placeholder="عنوان (Markdown مجاز نیست)" value={title} onChange={(e) => setTitle(e.target.value)} />
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setMode("edit")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${mode === "edit" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"}`}
            >
              ویرایش
            </button>
            <button
              type="button"
              onClick={() => setMode("preview")}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${mode === "preview" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"}`}
            >
              پیش‌نمایش
            </button>
          </div>
          {mode === "edit" ? (
            <textarea
              dir="rtl"
              className="min-h-[140px] w-full rounded-xl border border-input bg-background px-4 py-3 font-mono text-sm leading-7 shadow-sm outline-none focus:ring-2 focus:ring-ring"
              placeholder="متن Markdown… (## عنوان، **پررنگ**، - فهرست)"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
          ) : (
            <div className="min-h-[140px] rounded-xl border border-border bg-muted/20 p-4">
              <MarkdownView source={body} />
            </div>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <select
              className="rounded-xl border border-input bg-background px-3 py-2 text-sm"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
            <Button size="sm" onClick={() => createMutation.mutate()} disabled={createMutation.isPending || title.trim().length < 3}>
              <Plus className="ml-1 h-4 w-4" /> ساخت پیش‌نویس
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-dashed p-3">
            <Sparkles className="h-4 w-4 text-primary" />
            <Input
              dir="rtl"
              className="w-64"
              placeholder="موضوع مقاله برای تولید با AI…"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
            <Button
              size="sm"
              variant="outline"
              disabled={aiDraftMutation.isPending || topic.trim().length < 3}
              onClick={() => aiDraftMutation.mutate()}
            >
              <Sparkles className="ml-1 h-3.5 w-3.5" /> تولید پیش‌نویس با AI
            </Button>
          </div>
        </CardContent>
      </Card>

      {rows.length > 0 && (
        <Card>
          <CardContent className="divide-y divide-border p-0">
            {rows.map((item) => (
              <div key={item.id} className="px-6 py-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="flex flex-wrap items-center gap-2 text-sm font-semibold text-foreground">
                      {item.title}
                      {item.generated_by_ai && (
                        <Badge variant="secondary">
                          <Bot className="ml-1 h-3 w-3" /> تولید AI
                        </Badge>
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {CATEGORY_LABELS[item.category] ?? item.category} — {item.body.slice(0, 60)}…
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={STATUS_BADGE[item.status] ?? "secondary"}>
                      {item.status === "published" ? "منتشر شده" : item.status === "archived" ? "بایگانی" : "پیش‌نویس"}
                    </Badge>
                    {item.rag_synced && <Badge variant="success">RAG ✓</Badge>}
                    <Button size="sm" variant="outline" onClick={() => setActiveId(activeId === item.id ? null : item.id)}>
                      <History className="ml-1 h-3.5 w-3.5" /> نسخه‌ها/ترجمه
                    </Button>
                    {item.status === "draft" && (
                      <Button size="sm" variant="outline" onClick={() => publishMutation.mutate(item.id)}>
                        <Send className="ml-1 h-3.5 w-3.5" /> انتشار
                      </Button>
                    )}
                  </div>
                </div>

                {activeId === item.id && (
                  <div className="mt-4 grid gap-4 rounded-xl border border-border bg-muted/10 p-4 lg:grid-cols-2">
                    <div>
                      <p className="mb-2 flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
                        <Languages className="h-3.5 w-3.5" /> ترجمه AI
                      </p>
                      <div className="flex flex-wrap items-center gap-2">
                        <select
                          className="rounded-lg border border-input bg-background px-2 py-1.5 text-sm"
                          value={lang}
                          onChange={(e) => setLang(e.target.value)}
                        >
                          {LANGUAGES.map(([code, label]) => (
                            <option key={code} value={code}>{label}</option>
                          ))}
                        </select>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={translateMutation.isPending}
                          onClick={() => translateMutation.mutate({ id: item.id, language: lang })}
                        >
                          ترجمه
                        </Button>
                      </div>
                      <ul className="mt-3 space-y-1">
                        {(translationsQuery.data ?? []).map((tr) => (
                          <li key={tr.language} className="text-xs text-muted-foreground">
                            <b>{LANGUAGES.find(([c]) => c === tr.language)?.[1] ?? tr.language}</b> — {tr.title}
                          </li>
                        ))}
                        {(translationsQuery.data ?? []).length === 0 && (
                          <li className="text-xs text-muted-foreground">ترجمه‌ای ثبت نشده.</li>
                        )}
                      </ul>
                    </div>
                    <div>
                      <p className="mb-2 flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
                        <CalendarClock className="h-3.5 w-3.5" /> انتشار زمان‌بندی‌شده
                      </p>
                      <div className="flex flex-wrap items-center gap-2">
                        <Input
                          dir="ltr"
                          type="datetime-local"
                          className="w-56 text-xs"
                          value={scheduleAt}
                          onChange={(e) => setScheduleAt(e.target.value)}
                        />
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={!scheduleAt || scheduleMutation.isPending}
                          onClick={() =>
                            scheduleMutation.mutate({
                              id: item.id,
                              at: new Date(scheduleAt).toISOString(),
                            })
                          }
                        >
                          زمان‌بندی
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => cancelScheduleMutation.mutate(item.id)}>
                          لغو
                        </Button>
                      </div>
                      <p className="mt-2 text-xs text-muted-foreground">
                        {item.scheduled_at ? `زمان‌بندی: ${new Date(item.scheduled_at).toLocaleString("fa-IR")}` : "زمان‌بندی فعالی ندارد."}
                      </p>
                      <p className="mb-2 mt-4 flex items-center gap-1.5 text-xs font-bold text-muted-foreground">
                        <History className="h-3.5 w-3.5" /> تاریخچه نسخه‌ها
                      </p>
                      <ul className="space-y-1">
                        {(versionsQuery.data ?? []).map((v) => (
                          <li key={v.version} className="text-xs text-muted-foreground">
                            نسخه {v.version} — {v.title.slice(0, 40)}
                          </li>
                        ))}
                        {(versionsQuery.data ?? []).length === 0 && (
                          <li className="text-xs text-muted-foreground">نسخه‌ای ثبت نشده.</li>
                        )}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
