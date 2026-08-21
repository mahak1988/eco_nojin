"use client";

import Link from "next/link";
import { Leaf } from "lucide-react";

import { siteRegistry, SITE_GROUPS } from "@/lib/site-registry";
import { useI18n } from "@/lib/i18n-context";
import { groupTitle, entryTitle } from "@/lib/site-i18n";

export default function SiteFooter() {
  const { t, locale, direction } = useI18n();

  return (
    <footer className="border-t border-border bg-muted/30" dir={direction}>
      <div className="mx-auto max-w-6xl px-4 py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="space-y-3 md:col-span-1">
            <p className="flex items-center gap-2 font-bold text-foreground">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Leaf className="h-4 w-4" />
              </span>
              اکو نوژین
            </p>
            <p className="text-sm leading-7 text-muted-foreground">{t("footer_tagline")}</p>
          </div>

          {SITE_GROUPS.map((group) => {
            const items = Object.values(siteRegistry)
              .filter((e) => e.group === group.key)
              .slice(0, 8);
            if (items.length === 0) return null;
            return (
              <div key={group.key} className="space-y-2">
                <h3 className="text-sm font-bold text-foreground">{groupTitle(group.key, locale)}</h3>
                <ul className="space-y-1.5">
                  {items.map((e) => (
                    <li key={e.path}>
                      <Link
                        href={`/${e.path}`}
                        className="text-xs leading-5 text-muted-foreground transition-colors hover:text-primary"
                      >
                        {entryTitle(e.path, e.title, locale)}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-3 border-t border-border pt-6 text-xs text-muted-foreground sm:flex-row">
          <p>{t("footer_rights_line")}</p>
          <div className="flex gap-4">
            <Link href="/legal/terms" className="transition-colors hover:text-primary">{t("footer_legal_terms")}</Link>
            <Link href="/legal/privacy" className="transition-colors hover:text-primary">{t("footer_legal_privacy")}</Link>
            <Link href="/legal/security" className="transition-colors hover:text-primary">{t("footer_legal_security")}</Link>
            <Link href="/pages" className="transition-colors hover:text-primary">{t("nav_all_pages")}</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
