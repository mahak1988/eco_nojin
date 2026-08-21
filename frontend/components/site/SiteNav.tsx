"use client";

import Link from "next/link";
import { Leaf, Menu, Search, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { siteRegistry, SITE_GROUPS } from "@/lib/site-registry";
import { useI18n } from "@/lib/i18n-context";
import { groupTitle, entryTitle } from "@/lib/site-i18n";

const NAV_GROUP_KEYS = [
  "services",
  "learn",
  "tools",
  "modules",
  "science",
  "community",
  "admin",
  "account",
];

function groupItems(groupKey: string) {
  return Object.values(siteRegistry)
    .filter((e) => e.group === groupKey)
    .slice(0, 8);
}

export default function SiteNav() {
  const { t, locale, direction } = useI18n();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4" dir={direction}>
        <Link href="/" className="flex items-center gap-2 font-bold text-foreground">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Leaf className="h-5 w-5" />
          </span>
          <span className="text-lg">اکو نوژین</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-1 lg:flex">
          {NAV_GROUP_KEYS.map((key) => {
            const items = groupItems(key);
            const home = items.find((i) => i.path === key) ?? items[0];
            const title = groupTitle(key, locale);
            return (
              <DropdownMenu key={key}>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="text-sm">
                    {title}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-64">
                  <DropdownMenuLabel>{title}</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {home && (
                    <DropdownMenuItem asChild>
                      <Link href={`/${home.path}`}>{entryTitle(home.path, home.title, locale)}</Link>
                    </DropdownMenuItem>
                  )}
                  {items
                    .filter((i) => i.path !== key)
                    .map((i) => (
                      <DropdownMenuItem key={i.path} asChild>
                        <Link href={`/${i.path}`} className="line-clamp-1">
                          {entryTitle(i.path, i.title, locale)}
                        </Link>
                      </DropdownMenuItem>
                    ))}
                </DropdownMenuContent>
              </DropdownMenu>
            );
          })}
          <Link
            href="/search"
            className="flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            <Search className="h-4 w-4" />
            {t("nav_search")}
          </Link>
          <Link href="/pages" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
            {t("nav_all_pages")}
          </Link>
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <Link href="/login">
            <Button variant="ghost" size="sm">{t("nav_login")}</Button>
          </Link>
          <Link href="/register">
            <Button size="sm">{t("nav_register")}</Button>
          </Link>
        </div>

        {/* Mobile toggle */}
        <button
          type="button"
          className="rounded-lg p-2 lg:hidden"
          onClick={() => setMobileOpen((v) => !v)}
          aria-label={t("nav_menu") || "منو"}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="border-t border-border bg-background px-4 py-4 lg:hidden" dir={direction}>
          <div className="grid grid-cols-2 gap-2">
            {SITE_GROUPS.map((g) => (
              <Link
                key={g.key}
                href={`/pages#${g.key}`}
                className="rounded-xl border border-border px-3 py-2 text-sm transition-colors hover:border-primary"
                onClick={() => setMobileOpen(false)}
              >
                {groupTitle(g.key, locale)}
              </Link>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
