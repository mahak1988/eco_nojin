#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_hooks_export.py — export hooks from @eco/i18n index + clean LanguageSwitcher.

Root cause: hooks.ts always existed but was NEVER re-exported from
packages/i18n/src/index.ts. The previous migration script removed the legacy
exports AND assumed hooks were importable — they weren't. Fix:
  1. add hook re-exports to index.ts
  2. write a clean, correct LanguageSwitcher (4 languages, RTL-aware)
  3. sanity-check: list every export of index.ts
"""

from pathlib import Path

ROOT = Path(r"D:\eco_nojin\frontend")


def say(m):
    print(m, flush=True)


def main():
    # ---- 1. index.ts: re-export hooks ----
    say("[1] index.ts — re-export hooks")
    idx = ROOT / "packages" / "i18n" / "src" / "index.ts"
    t = idx.read_text(encoding="utf-8")
    if "useLocale" not in t:
        t += (
            "\n"
            "// hooks (added by fix_hooks_export) — the official i18next API\n"
            "export { useLocale, useSwitchLocale, useIsRtl, "
            "useDocumentDirection } from './hooks';\n"
        )
        idx.write_text(t, encoding="utf-8")
        say("    hooks re-exports ADDED")
    else:
        say("    already exported")
    say("    --- index.ts now ---")
    for ln in idx.read_text(encoding="utf-8").splitlines():
        say("      " + ln)

    # ---- 2. clean LanguageSwitcher ----
    say("[2] rewrite LanguageSwitcher (web app)")
    content = """\
import { useLocale, useSwitchLocale } from '@eco/i18n';
import { useTranslation } from 'react-i18next';

const LANGS = [
  { code: 'fa', label: 'فارسی' },
  { code: 'en', label: 'English' },
  { code: 'ar', label: 'العربية' },
  { code: 'ur', label: 'اردو' },
] as const;

export function LanguageSwitcher() {
  const { locale } = useLocale();
  const switchTo = useSwitchLocale();
  const { t } = useTranslation();

  return (
    <label className="flex items-center gap-1">
      <span className="sr-only">{t('common.language', 'Language')}</span>
      <select
        value={locale}
        onChange={(e) => {
          e.preventDefault();
          switchTo(e.target.value as typeof locale);
        }}
        className="rounded-lg border border-ink/10 bg-surface px-2 py-1.5 text-sm text-ink focus:border-brand-400 focus:outline-none"
        aria-label={t('common.language', 'Language')}
      >
        {LANGS.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>
    </label>
  );
}
"""
    p = ROOT / "apps" / "web" / "src" / "app" / "LanguageSwitcher.tsx"
    p.write_text(content, encoding="utf-8", newline="\n")
    say("    rewritten (4 languages, select-based)")

    # dashboard variant check
    dash = ROOT / "apps" / "dashboard" / "src" / "app" / "LanguageSwitcher.tsx"
    if dash.exists():
        say("    (dashboard also has a LanguageSwitcher — checking its imports)")
        dt = dash.read_text(encoding="utf-8", errors="replace")
        if "useI18n" in dt:
            say("      dashboard one still uses useI18n — will fix next round")
        else:
            say("      dashboard one OK")

    say("")
    say("DONE — now run:")
    say("  pnpm -C frontend dev   (page should render, no module error)")
    say("  pnpm -C frontend build (proof) then commit+push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())