"use client";

import { useState } from "react";
import { CheckCircle2, XCircle, Award } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getQuiz } from "@/lib/quiz-data";
import {
  answerQuizQuestion,
  loadLearning,
  saveLearning,
} from "@/lib/learning-store";

const XP_PER_CORRECT = 10;

export default function Quiz({ category }: { category: string }) {
  const questions = getQuiz(category);
  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [finished, setFinished] = useState(false);

  if (questions.length === 0) return null;

  const q = questions[current];
  const answered = selected !== null;
  const isCorrect = answered && selected === q.correct;

  const pick = (i: number) => {
    if (answered) return;
    setSelected(i);
    if (i === q.correct) {
      const state = loadLearning();
      const { state: next, awarded } = answerQuizQuestion(state, q.id, XP_PER_CORRECT);
      if (awarded > 0) {
        saveLearning(next);
        setCorrectCount((c) => c + 1);
        toast.success(`پاسخ درست! +${awarded} امتیاز`);
      } else {
        setCorrectCount((c) => c + 1);
        toast.success("پاسخ درست!");
      }
    }
  };

  const next = () => {
    if (current + 1 >= questions.length) {
      setFinished(true);
    } else {
      setCurrent((c) => c + 1);
      setSelected(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Award className="h-5 w-5 text-primary" />
            آزمون این درس
          </span>
          <Badge variant="secondary">
            {finished ? "پایان" : `${current + 1} از ${questions.length}`} — درست: {correctCount}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!finished ? (
          <>
            <p className="font-semibold text-foreground">{q.question}</p>
            <div className="grid gap-2">
              {q.options.map((opt, i) => {
                let cls =
                  "justify-start rounded-xl border border-border bg-background px-4 py-3 text-right text-sm transition-colors";
                if (answered && i === q.correct) cls += " border-emerald-500 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400";
                else if (answered && i === selected) cls += " border-destructive bg-destructive/10 text-destructive";
                else cls += " hover:border-primary";
                return (
                  <button key={i} className={cls} onClick={() => pick(i)} disabled={answered}>
                    <span className="flex items-center gap-2">
                      {answered && i === q.correct && <CheckCircle2 className="h-4 w-4" />}
                      {answered && i === selected && i !== q.correct && <XCircle className="h-4 w-4" />}
                      {opt}
                    </span>
                  </button>
                );
              })}
            </div>
            {answered && (
              <div className="space-y-3">
                <p className="rounded-xl bg-muted/40 p-3 text-sm leading-7 text-muted-foreground">
                  📖 {q.explanation}
                </p>
                <Button onClick={next}>{current + 1 >= questions.length ? "پایان آزمون" : "سؤال بعدی"}</Button>
              </div>
            )}
          </>
        ) : (
          <div className="space-y-3 text-center">
            <p className="text-lg font-bold text-foreground">
              نتیجه: {correctCount} از {questions.length}
            </p>
            <p className="text-sm text-muted-foreground">
              {correctCount === questions.length
                ? "عالی! دانش شما در این حوزه کامل است 🌟"
                : "با مرور مقاله‌های این درس، دوباره تلاش کنید."}
            </p>
            <Button
              variant="outline"
              onClick={() => {
                setCurrent(0);
                setSelected(null);
                setCorrectCount(0);
                setFinished(false);
              }}
            >
              آزمون دوباره
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
