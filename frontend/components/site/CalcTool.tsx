"use client";

import { useState } from "react";
import { Calculator } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getCalculator } from "@/lib/calculators";

export default function CalcTool({ id }: { id: string }) {
  const calc = getCalculator(id);
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<{ result: string; note: string } | null>(null);

  if (!calc) {
    return <p className="text-destructive">ماشین‌حساب یافت نشد: {id}</p>;
  }

  const run = () => {
    const parsed: Record<string, number> = {};
    let valid = true;
    for (const f of calc.fields) {
      const raw = values[f.key];
      const n = raw === undefined || raw === "" ? NaN : Number(raw.replace(",", "."));
      if (!Number.isFinite(n)) {
        valid = false;
        break;
      }
      parsed[f.key] = n;
    }
    if (!valid) {
      setResult({ result: "لطفاً همه مقادیر را وارد کنید.", note: "" });
      return;
    }
    setResult(calc.compute(parsed));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Calculator className="h-5 w-5 text-primary" />
          {calc.title}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{calc.formula}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          {calc.fields.map((f) => (
            <label key={f.key} className="block space-y-1.5">
              <span className="text-sm text-foreground">
                {f.label} {f.unit && <span className="text-xs text-muted-foreground">({f.unit})</span>}
              </span>
              <Input
                inputMode="decimal"
                dir="ltr"
                placeholder={f.placeholder}
                value={values[f.key] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
              />
            </label>
          ))}
        </div>

        <Button onClick={run}>محاسبه</Button>

        {result && (
          <div className="space-y-2 rounded-xl border border-border bg-muted/30 p-4">
            <p className="font-semibold text-foreground">{result.result}</p>
            {result.note && <p className="text-xs leading-6 text-muted-foreground">📌 {result.note}</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
