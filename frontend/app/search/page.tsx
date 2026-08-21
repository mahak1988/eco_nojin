"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Search, BookOpen, Loader2 } from "lucide-react";

import SitePage from "@/components/site/SitePage";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { siteRegistry } from "@/lib/site-registry";
import { apiUrl } from "@/lib/config";

interface KnowledgeResult {
  query: string;
  answer: string;
  sources: { id: string; title: string; source: string }[];
  confidence: number;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [knowledge, setKnowledge] = useState<KnowledgeResult | null>(null);
  const [loading, setLoading] = useState(false);

  const siteResults = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (q.length < 2) return [];
    return Object.values(siteRegistry)
      .filter(
        (e) =>
          e.title.toLowerCase().includes(q) ||
          e.description.toLowerCase().includes(q)
      )
      .slice(0, 12);
  }, [query]);

  const askKnowledge = async () => {
    if (query.trim().length < 3) return;
    setLoading(true);
    try {
      const res = await fetch(apiUrl("/api/v1/ai/chat"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: query }),
      });
      if (!res.ok) throw new Error(`خطا (${res.status})`);
      setKnowledge(await res.json());
    } catch (e) {
      setKnowledge({
        query,
        answer: "پشتیبان دانش در دسترس نیست. دوباره تلاش کنید.",
        sources: [],
        confidence: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <SitePage
      title="جستجو در اکو نوژین"
      description="جستجو میان ۱۵۰+ صفحه پلتفرم، یا پرسش از دانشنامه علمی با پاسخ مستند."
      badge="جستجو"
      related={["pages", "learn", "tools", "services/advisory"]}
    >
      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          dir="rtl"
          placeholder="مثلاً: آبیاری قطره‌ای، کربن خاک، کمپوست…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && askKnowledge()}
        />
        <Button onClick={askKnowledge} disabled={loading} className="shrink-0">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          جستجو
        </Button>
      </div>

      {siteResults.length > 0 && (
        <section className="space-y-3">
          <h2 className="flex items-center gap-2 text-lg font-bold text-foreground">
            <BookOpen className="h-5 w-5 text-primary" />
            صفحات مرتبط ({siteResults.length})
          </h2>
          <div className="grid gap-2 sm:grid-cols-2">
            {siteResults.map((e) => (
              <Link key={e.path} href={`/${e.path}`}>
                <Card className="h-full transition-shadow hover:shadow-md">
                  <CardContent className="space-y-1 p-4">
                    <p className="text-sm font-semibold text-foreground">{e.title}</p>
                    <p className="line-clamp-2 text-xs text-muted-foreground">{e.description}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      )}

      {knowledge && (
        <section className="space-y-3 rounded-2xl border border-border bg-muted/20 p-5">
          <h2 className="text-lg font-bold text-foreground">پاسخ دانشنامه</h2>
          <p className="whitespace-pre-line text-sm leading-8 text-foreground/90">{knowledge.answer}</p>
          {knowledge.sources.length > 0 && (
            <ul className="space-y-1 border-t border-border pt-3 text-xs text-muted-foreground">
              {knowledge.sources.map((s) => (
                <li key={s.id}>
                  {s.title} — {s.source}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </SitePage>
  );
}
