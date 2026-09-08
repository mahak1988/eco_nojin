#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_i18n_migrate.py — repair the mis-pasted i18n.tsx + migrate useI18n consumers.

1. RESTORE packages/i18n/src/i18n.tsx to its original (dual-system legacy)
   content — the LanguageSwitcher sample was pasted there by mistake.
2. SCAN apps/ + packages/ for real useI18n consumers (excluding the i18n
   package itself).
3. REWRITE each consumer: useI18n -> react-i18next useTranslation + hooks.
4. Remove I18nProvider/useI18n export from i18n index.ts (guard: crash
   class becomes impossible).
5. Report everything; build is NOT run here (run it manually after review).
"""

import re
from pathlib import Path

ROOT = Path(r"D:\eco_nojin\frontend")

# Original i18n.tsx content (restored from the session's earlier dump)
I18N_TSX = """import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import fa from './locales/fa';
import en from './locales/en';

export type Lang = 'fa' | 'en';
type Dict = Record<string, unknown>;
const DICTS: Record<Lang, Dict> = { fa, en };

function lookup(dict: Dict, path: string): string | undefined {
  let cur: unknown = dict;
  for (const part of path.split('.')) {
    if (typeof cur !== 'object' || cur === null) return undefined;
    cur = (cur as Dict)[part];
  }
  return typeof cur === 'string' ? cur : undefined;
}

interface I18nValue { lang: Lang; dir: 'rtl' | 'ltr'; setLang: (l: Lang) => void; t: (key: string) => string; }
const Ctx = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() =>
    typeof window !== 'undefined' && window.localStorage.getItem('eco_lang') === 'en' ? 'en' : 'fa');
  const dir: 'rtl' | 'ltr' = lang === 'fa' ? 'rtl' : 'ltr';

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
    window.localStorage.setItem('eco_lang', lang);
  }, [lang, dir]);

  const value = useMemo<I18nValue>(() => ({
    lang, dir, setLang,
    t: (key) => lookup(DICTS[lang], key) ?? lookup(DICTS.en, key) ?? key,
  }), [lang]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useI18n must be used within <I18nProvider>');
  return ctx;
}
"""


def say(m):
    print(m, flush=True)


def main():
    # ---------- 1. restore i18n.tsx ----------
    say("[1] restore packages/i18n/src/i18n.tsx (was overwritten by mistake)")
    p = ROOT / "packages" / "i18n" / "src" / "i18n.tsx"
    p.write_text(I18N_TSX, encoding="utf-8", newline="\n")
    say("    restored original legacy module")

    # ---------- 2. scan consumers ----------
    say("[2] scan for useI18n consumers (apps/ + packages/, excl. i18n pkg & node_modules)")
    hits = []
    for base in (ROOT / "apps", ROOT / "packages"):
        for f in base.rglob("*.tsx"):
            if "node_modules" in f.parts:
                continue
            if "packages" in f.parts and "i18n" in f.parts:
                continue
            try:
                t = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if re.search(r"\buseI18n\b", t) or "I18nProvider" in t:
                hits.append((f, t))
    say(f"    consumers found: {len(hits)}")
    for f, _ in hits:
        say(f"      - {f.relative_to(ROOT)}")

    # ---------- 3. migrate each consumer ----------
    say("[3] migrate consumers to react-i18next")
    for f, t in hits:
        orig = t
        # import line: replace useI18n import with hooks import
        t = re.sub(
            r"import\s*\{[^}]*useI18n[^}]*\}\s*from\s*'@eco/i18n';?",
            "import { useLocale, useSwitchLocale } from '@eco/i18n';",
            t,
        )
        # add useTranslation import if missing
        if "useTranslation" not in t:
            t = re.sub(
                r"(^import .*?\n)",
                r"\1import { useTranslation } from 'react-i18next';\n",
                t, count=1,
            )
        # usage: destructure
        t = re.sub(
            r"const\s*\{([^}]*)\}\s*=\s*useI18n\(\)",
            lambda m: "const { t } = useTranslation(); const { locale, dir } = useLocale();",
            t,
        )
        # common variable renames
        t = t.replace("lang ===", "locale ===").replace("setLang(", "switchTo(")
        # if switchTo defined via hook:
        if "switchTo(" in t and "useSwitchLocale" in t:
            t = re.sub(
                r"const\s*\{\s*locale,\s*dir\s*\}\s*=\s*useLocale\(\);",
                "const { locale, dir } = useLocale(); const switchTo = useSwitchLocale();",
                t, count=1,
            )
        if t != orig:
            f.write_text(t, encoding="utf-8")
            say(f"    migrated: {f.relative_to(ROOT)}")
        else:
            say(f"    (no textual change — manual check): {f.relative_to(ROOT)}")

    # ---------- 4. guard: remove legacy exports from index ----------
    say("[4] remove legacy I18nProvider/useI18n exports from index.ts")
    idx = ROOT / "packages" / "i18n" / "src" / "index.ts"
    t = idx.read_text(encoding="utf-8")
    lines = t.split("\n")
    keep = [l for l in lines if "useI18n" not in l and "I18nProvider" not in l]
    if len(keep) != len(lines):
        idx.write_text("\n".join(keep), encoding="utf-8")
        say(f"    removed {len(lines) - len(keep)} legacy export line(s)")
    else:
        say("    nothing to remove (already clean)")

    say("")
    say("DONE — next steps (manual):")
    say("  1. review the migrated files listed above in VS Code")
    say("  2. pnpm -C frontend build")
    say("  3. git add + commit + push (pattern as usual)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())