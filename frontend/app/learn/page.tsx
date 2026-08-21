"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { GraduationCap, Leaf, Sparkles, Trophy, FlaskConical } from "lucide-react";
import { toast } from "sonner";

import { apiUrl } from "@/lib/config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  completeModule,
  levelFor,
  loadLearning,
  saveLearning,
  XP_PER_LEVEL,
} from "@/lib/learning-store";

/* ------------------------------------------------------------------ */
/* Types (mirror the FastAPI QueryResponse contract)                   */
/* ------------------------------------------------------------------ */
interface Source {
  id: string;
  title: string;
  source: string;
  category: string;
  relevance: number;
}
interface QueryResponse {
  query: string;
  answer: string;
  sources: Source[];
  confidence: number;
}

/* ------------------------------------------------------------------ */
/* Expert question form (react-hook-form + zod)                        */
/* ------------------------------------------------------------------ */
const questionSchema = z.object({
  question: z
    .string()
    .min(5, "سؤال باید حداقل ۵ حرف باشد")
    .max(1000, "سؤال نباید بیشتر از ۱۰۰۰ حرف باشد"),
});
type QuestionForm = z.infer<typeof questionSchema>;

/* ------------------------------------------------------------------ */
/* Learning modules (⭐7 educational gamification)                      */
/* ------------------------------------------------------------------ */
interface LearningModule {
  id: string;
  title: string;
  description: string;
  xp: number;
}
const MODULES: LearningModule[] = [
  { id: "compost", title: "کمپوست و نسبت کربن به نیتروژن", description: "چرا نسبت C/N بین ۲۵ تا ۳۵ بهینه است؟", xp: 30 },
  { id: "irrigation", title: "آبیاری قطره‌ای و تبخیر", description: "اصول FAO-56 و محاسبه نیاز آبی گیاه", xp: 40 },
  { id: "soil", title: "سلامت خاک", description: "pH، ماده آلی و عناصر غذایی", xp: 30 },
  { id: "carbon", title: "کربن خاک و اقلیم", description: "نقش خاک در ترسیب کربن", xp: 40 },
];

export default function LearnPage() {
  const [state, setState] = useState(() => loadLearning());

  // Sync from storage on mount (client-only)
  useEffect(() => {
    setState(loadLearning());
  }, []);

  function handleComplete(module: LearningModule) {
    const next = completeModule(state, module.id, module.xp);
    if (next !== state) {
      setState(next);
      saveLearning(next);
      toast.success(`ماژول «${module.title}» تکمیل شد — ${module.xp} امتیاز!`);
    }
  }

  /* ------------------------------------------------------------------ */
  /* Expert form                                                         */
  /* ------------------------------------------------------------------ */
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<QuestionForm>({ resolver: zodResolver(questionSchema) });

  const askMutation = useMutation({
    mutationFn: async (question: string): Promise<QueryResponse> => {
      const res = await fetch(apiUrl("/api/v1/ai/chat"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) {
        throw new Error(`پاسخ‌گو در دسترس نیست (${res.status})`);
      }
      return res.json();
    },
    onSuccess: () => reset(),
  });

  const healthQuery = useQuery({
    queryKey: ["ai-health"],
    queryFn: async (): Promise<{ status: string }> => {
      const res = await fetch(apiUrl("/api/v1/ai/health"));
      if (!res.ok) throw new Error("health failed");
      return res.json();
    },
    retry: 1,
  });

  const onSubmit = handleSubmit((values) => {
    askMutation.mutate(values.question);
  });

  const level = levelFor(state.xp);
  const levelProgress = ((state.xp % XP_PER_LEVEL) / XP_PER_LEVEL) * 100;

  return (
    <div dir="rtl" className="min-h-screen bg-gradient-to-b from-background to-muted/40 px-4 py-10">
      <div className="mx-auto max-w-3xl space-y-8">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold text-foreground">
              <GraduationCap className="h-6 w-6 text-primary" />
              یادگیری اکو نوژین
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              آموزش علمی کشاورزی اقلیم‌هوشمند — با پیشرفت گام‌به‌گام
            </p>
          </div>
          <Badge variant={healthQuery.isSuccess ? "success" : "warning"}>
            {healthQuery.isSuccess ? "پشتیبان هوش مصنوعی: آنلاین" : "پشتیبان هوش مصنوعی: آفلاین"}
          </Badge>
        </header>

        {/* Level card */}
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-amber-500" />
              سطح {level} — {state.xp} امتیاز
            </CardTitle>
            <Badge variant="secondary">پیشرفت در این مرورگر ذخیره می‌شود</Badge>
          </CardHeader>
          <CardContent>
            <Progress value={levelProgress} />
            <p className="mt-2 text-xs text-muted-foreground">
              {XP_PER_LEVEL - (state.xp % XP_PER_LEVEL)} امتیاز تا سطح بعدی
            </p>
          </CardContent>
        </Card>

        {/* Modules */}
        <div className="grid gap-4 sm:grid-cols-2">
          {MODULES.map((module) => {
            const done = state.completed.includes(module.id);
            return (
              <Card key={module.id} className={done ? "opacity-75" : undefined}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    {done ? <Leaf className="h-5 w-5 text-emerald-500" /> : <FlaskConical className="h-5 w-5 text-primary" />}
                    {module.title}
                  </CardTitle>
                  <CardDescription>{module.description}</CardDescription>
                </CardHeader>
                <CardContent className="flex items-center justify-between">
                  <Badge variant={done ? "success" : "secondary"}>{done ? "تکمیل شد ✓" : `+${module.xp} امتیاز`}</Badge>
                  <Button size="sm" variant={done ? "outline" : "default"} disabled={done} onClick={() => handleComplete(module)}>
                    {done ? "انجام شد" : "تکمیل کردم"}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Expert question */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              پرسش از کارشناس
            </CardTitle>
            <CardDescription>
              پاسخ بر پایه دانشنامه علمی (FAO و همکاران) با ذکر منبع — بدون محتوای ساختگی
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row">
              <Input
                placeholder="مثلاً: نسبت کربن به نیتروژن کمپوست چقدر باید باشد؟"
                {...register("question")}
                aria-invalid={!!errors.question}
              />
              <Button type="submit" disabled={askMutation.isPending} className="shrink-0">
                {askMutation.isPending ? "در حال پاسخ…" : "بپرس"}
              </Button>
            </form>
            {errors.question && (
              <p className="text-sm text-destructive">{errors.question.message}</p>
            )}

            {askMutation.isError && (
              <p className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">
                {askMutation.error instanceof Error ? askMutation.error.message : "خطا در ارتباط با پشتیبان"}
              </p>
            )}

            {askMutation.data && (
              <div className="space-y-3 rounded-xl border border-border bg-muted/30 p-4">
                <p className="whitespace-pre-line text-sm leading-7">{askMutation.data.answer}</p>
                {askMutation.data.sources.length > 0 && (
                  <div className="space-y-1 border-t border-border pt-3">
                    <p className="text-xs font-semibold text-muted-foreground">منابع:</p>
                    {askMutation.data.sources.map((s) => (
                      <p key={s.id} className="text-xs text-muted-foreground">
                        {s.title} — {s.source} (ارتباط: {(s.relevance * 100).toFixed(0)}٪)
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
