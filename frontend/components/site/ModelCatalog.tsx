"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Atom, BookOpen, Play, ShieldCheck, FlaskConical, Layers } from "lucide-react";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import MarkdownView from "@/components/site/MarkdownView";

interface ParamSpec {
  name: string;
  label: string;
  unit: string;
  default?: number | null;
  kind: string;
}

interface ModelInfo {
  slug: string;
  name_fa: string;
  name_en: string;
  domain: string;
  fidelity: string;
  reference: string;
  description: string;
  validity?: string;
  limitations?: string;
  params: ParamSpec[];
}

interface RunResult {
  slug: string;
  fidelity: string;
  result: unknown;
  executed_ms: number;
}

const FIDELITY_META: Record<string, { label: string; variant: "success" | "warning" | "secondary"; icon: typeof ShieldCheck }> = {
  official: { label: "رسمی", variant: "success", icon: ShieldCheck },
  simplified: { label: "ساده‌شده", variant: "secondary", icon: Layers },
  experimental: { label: "آزمایشی", variant: "warning", icon: FlaskConical },
};

const DOMAIN_LABELS: Record<string, string> = {
  crop: "محصول",
  water: "آب",
  soil: "خاک",
  carbon: "کربن",
  climate: "اقلیم",
};

export default function ModelCatalog() {
  const [open, setOpen] = useState<string | null>(null);
  const [inputs, setInputs] = useState<Record<string, Record<string, string>>>({});
  const [outputs, setOutputs] = useState<Record<string, RunResult | string>>({});
  const [running, setRunning] = useState<string | null>(null);

  const modelsQuery = useQuery({
    queryKey: ["models"],
    queryFn: async (): Promise<{ count: number; models: ModelInfo[] }> => {
      const res = await fetch(apiUrl("/api/v1/models"));
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      return res.json();
    },
  });

  const data = modelsQuery.data;

  const cppQuery = useQuery({
    queryKey: ["cpp-status"],
    queryFn: async (): Promise<{ available: boolean; note?: string } | null> => {
      const res = await fetch(apiUrl("/api/v1/models/cpp-status"));
      return res.ok ? res.json() : null;
    },
  });

  const runModel = async (model: ModelInfo) => {
    const values = inputs[model.slug] ?? {};
    const params: Record<string, unknown> = {};
    for (const p of model.params) {
      const raw = values[p.name] ?? "";
      if (raw === "" && p.default !== undefined && p.default !== null) {
        params[p.name] = p.default;
      } else if (raw !== "") {
        params[p.name] = p.kind === "str" ? raw : Number(raw);
      }
    }
    setRunning(model.slug);
    try {
      const res = await fetch(apiUrl(`/api/v1/models/${model.slug}/run`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const body = await res.json();
      if (!res.ok) {
        setOutputs((o) => ({ ...o, [model.slug]: body.detail ?? `خطا (${res.status})` }));
      } else {
        setOutputs((o) => ({ ...o, [model.slug]: body }));
      }
    } catch (e) {
      setOutputs((o) => ({ ...o, [model.slug]: e instanceof Error ? e.message : "خطا" }));
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Atom className="h-5 w-5 text-primary" />
            کاتالوگ مدل‌های علمی (فاز ۷)
          </CardTitle>
          <CardDescription>
            {data ? `${data.count} مدل قابل فراخوانی با نشان وفاداری — رسمی / ساده‌شده / آزمایشی.` : "در حال بارگذاری…"}
          </CardDescription>
          {cppQuery.data && (
            <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/10 px-3 py-2 text-xs">
              <span className={cppQuery.data.available ? "text-emerald-600" : "text-amber-600"}>
                {cppQuery.data.available ? "⚙️ موتور C++20 فعال" : "⚙️ موتور C++20 در دسترس نیست"}
              </span>
              <span className="text-muted-foreground">{cppQuery.data.note}</span>
            </div>
          )}
        </CardHeader>
      </Card>

      {data?.models.map((m) => {
        const meta = FIDELITY_META[m.fidelity] ?? FIDELITY_META.simplified;
        const FidelityIcon = meta.icon;
        const expanded = open === m.slug;
        const out = outputs[m.slug];
        return (
          <Card key={m.slug}>
            <CardContent className="p-0">
              <button
                type="button"
                className="flex w-full flex-wrap items-center justify-between gap-3 px-6 py-4 text-right"
                onClick={() => setOpen(expanded ? null : m.slug)}
              >
                <div className="min-w-0">
                  <p className="flex flex-wrap items-center gap-2 font-semibold text-foreground">
                    {m.name_fa}
                    <span className="text-xs font-normal text-muted-foreground" dir="ltr">
                      {m.name_en}
                    </span>
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {DOMAIN_LABELS[m.domain] ?? m.domain} — {m.reference}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={meta.variant}>
                    <FidelityIcon className="ml-1 h-3 w-3" />
                    {meta.label}
                  </Badge>
                </div>
              </button>

              {expanded && (
                <div className="space-y-3 border-t border-border px-6 py-4">
                  <p className="text-sm text-muted-foreground">{m.description}</p>
                  <div className="grid gap-2 rounded-xl border border-border bg-muted/10 p-3 text-xs sm:grid-cols-2">
                    <div>
                      <span className="font-bold text-foreground">دامنه اعتبار: </span>
                      <span className="text-muted-foreground">{m.validity ?? "—"}</span>
                    </div>
                    <div>
                      <span className="font-bold text-foreground">محدودیت‌ها: </span>
                      <span className="text-muted-foreground">{m.limitations ?? "—"}</span>
                    </div>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {m.params.map((p) => (
                      <label key={p.name} className="block">
                        <span className="mb-1 block text-xs text-muted-foreground">
                          {p.label} {p.unit ? `(${p.unit})` : ""}
                          {p.default !== undefined && p.default !== null ? ` — پیش‌فرض ${p.default}` : ""}
                        </span>
                        {p.kind === "str" ? (
                          <Input
                            dir="rtl"
                            className="text-sm"
                            placeholder={String(p.default ?? "")}
                            value={inputs[m.slug]?.[p.name] ?? ""}
                            onChange={(e) =>
                              setInputs((all) => ({
                                ...all,
                                [m.slug]: { ...(all[m.slug] ?? {}), [p.name]: e.target.value },
                              }))
                            }
                          />
                        ) : (
                          <Input
                            dir="ltr"
                            type="number"
                            className="text-sm"
                            placeholder={p.default !== undefined && p.default !== null ? String(p.default) : "—"}
                            value={inputs[m.slug]?.[p.name] ?? ""}
                            onChange={(e) =>
                              setInputs((all) => ({
                                ...all,
                                [m.slug]: { ...(all[m.slug] ?? {}), [p.name]: e.target.value },
                              }))
                            }
                          />
                        )}
                      </label>
                    ))}
                  </div>
                  <Button
                    size="sm"
                    disabled={running === m.slug}
                    onClick={() => runModel(m)}
                  >
                    <Play className="ml-1 h-3.5 w-3.5" /> اجرای مدل
                  </Button>
                  {out && (
                    <div className="rounded-xl border border-border bg-muted/20 p-3">
                      {typeof out === "string" ? (
                        <p className="text-sm font-medium text-destructive">{out}</p>
                      ) : (
                        <>
                          <p className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
                            <BookOpen className="h-3.5 w-3.5" />
                            نتیجه ({out.executed_ms} ms)
                          </p>
                          <pre
                            dir="ltr"
                            className="overflow-x-auto rounded-lg bg-background p-3 text-xs leading-6"
                          >
                            {JSON.stringify(out.result, null, 2)}
                          </pre>
                        </>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
