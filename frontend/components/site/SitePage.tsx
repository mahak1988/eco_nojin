import type { ReactNode } from "react";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

import SiteNav from "@/components/site/SiteNav";
import SiteFooter from "@/components/site/SiteFooter";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { siteRegistry, type SiteEntry, SITE_GROUPS } from "@/lib/site-registry";

export interface SiteSection {
  h?: string;
  p?: string[];
  bullets?: string[];
}

export interface SitePageProps {
  path?: string;
  title: string;
  description: string;
  badge?: string;
  sections?: SiteSection[];
  related?: string[];
  children?: ReactNode;
}

function Breadcrumbs({ path }: { path: string }) {
  const entry = siteRegistry[path];
  const group = entry ? SITE_GROUPS.find((g) => g.key === entry.group) : undefined;
  return (
    <nav aria-label="breadcrumb" className="mx-auto max-w-4xl px-4 pt-6">
      <ol className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
        <li>
          <Link href="/" className="transition-colors hover:text-primary">خانه</Link>
        </li>
        <ChevronLeft className="h-3 w-3 rtl:rotate-180" />
        {group && (
          <>
            <li>
              <Link href={`/pages#${group.key}`} className="transition-colors hover:text-primary">
                {group.title}
              </Link>
            </li>
            <ChevronLeft className="h-3 w-3 rtl:rotate-180" />
          </>
        )}
        <li aria-current="page" className="text-foreground/80">{entry?.title ?? ""}</li>
      </ol>
    </nav>
  );
}

function Section({ s }: { s: SiteSection }) {
  return (
    <section className="space-y-3">
      {s.h && <h2 className="text-xl font-bold text-foreground">{s.h}</h2>}
      {s.p?.map((para, i) => (
        <p key={i} className="leading-8 text-muted-foreground">
          {para}
        </p>
      ))}
      {s.bullets && (
        <ul className="grid gap-2">
          {s.bullets.map((b, i) => (
            <li key={i} className="flex items-start gap-2 leading-7 text-foreground/90">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
              {b}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function SitePage({
  path,
  title,
  description,
  badge,
  sections = [],
  related = [],
  children,
}: SitePageProps) {
  const relatedEntries: SiteEntry[] = related
    .map((p) => siteRegistry[p])
    .filter((e): e is SiteEntry => Boolean(e))
    .slice(0, 6);

  return (
    <div dir="rtl">
      <SiteNav />
      {path && <Breadcrumbs path={path} />}

      {/* Hero */}
      <header className="bg-gradient-to-b from-secondary/60 to-background px-4 pb-10 pt-10">
        <div className="mx-auto max-w-4xl space-y-4">
          {badge && <Badge variant="secondary">{badge}</Badge>}
          <h1 className="text-3xl font-extrabold leading-tight text-foreground sm:text-4xl">{title}</h1>
          <p className="max-w-2xl text-base leading-8 text-muted-foreground">{description}</p>
        </div>
      </header>

      {/* Body */}
      <main className="mx-auto max-w-4xl space-y-10 px-4 py-10">
        {sections.length > 0 && (
          <div className="space-y-10">
            {sections.map((s, i) => (
              <Section key={i} s={s} />
            ))}
          </div>
        )}

        {children}

        {relatedEntries.length > 0 && (
          <section className="space-y-4 border-t border-border pt-8">
            <h2 className="text-lg font-bold text-foreground">صفحات مرتبط</h2>
            <div className="grid auto-rows-fr gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {relatedEntries.map((entry) => (
                <Link key={entry.path} href={entry.path} className="block">
                  <Card className="h-full transition-shadow hover:shadow-md">
                    <CardContent className="p-4">
                      <p className="text-sm font-semibold text-foreground">{entry.title}</p>
                      <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{entry.description}</p>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Full site index — every page reachable from everywhere */}
        <section className="space-y-6 border-t border-border pt-8">
          <h2 className="text-lg font-bold text-foreground">فهرست کامل اکو نوژین</h2>
          {SITE_GROUPS.map((group) => {
            const entries = Object.values(siteRegistry).filter((e) => e.group === group.key);
            if (entries.length === 0) return null;
            return (
              <div key={group.key}>
                <h3 className="mb-2 text-sm font-bold text-muted-foreground">{group.title}</h3>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 sm:grid-cols-3 lg:grid-cols-4">
                  {entries.map((e) => (
                    <Link
                      key={e.path}
                      href={`/${e.path}`}
                      className="truncate text-sm text-foreground/80 transition-colors hover:text-primary"
                    >
                      {e.title}
                    </Link>
                  ))}
                </div>
              </div>
            );
          })}
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
