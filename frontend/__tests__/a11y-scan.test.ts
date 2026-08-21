import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

const ROOT = path.resolve(__dirname, "..");
const DIRS = ["app", "components", "lib"];

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const p = path.join(dir, entry);
    if (statSync(p).isDirectory()) {
      out.push(...walk(p));
    } else if (p.endsWith(".tsx") || p.endsWith(".ts")) {
      out.push(p);
    }
  }
  return out;
}

function srcFiles(): string[] {
  return DIRS.flatMap((d) => {
    const full = path.join(ROOT, d);
    try {
      return walk(full);
    } catch {
      return [];
    }
  });
}

describe("a11y static audit", () => {
  const files = srcFiles();
  it("finds no <img> without alt across app/components/lib", () => {
    const offenders: string[] = [];
    for (const f of files) {
      const t = readFileSync(f, "utf-8");
      for (const m of t.matchAll(/<img\b[^>]*>/g)) {
        if (!m[0].includes("alt=")) {
          offenders.push(`${path.relative(ROOT, f)}: ${m[0].slice(0, 80)}`);
        }
      }
    }
    expect(offenders).toEqual([]);
  });

  it("finds no icon-only <button> without an accessible name", () => {
    const offenders: string[] = [];
    for (const f of files) {
      const t = readFileSync(f, "utf-8");
      for (const m of t.matchAll(/<button\b([^>]*)>([^<]{0,10})<\/button>/gs)) {
        const [, attrs, inner] = m;
        if (!inner.trim() && !attrs.includes("aria-label") && !attrs.includes("title=")) {
          offenders.push(`${path.relative(ROOT, f)}: ${attrs.slice(0, 70)}`);
        }
      }
    }
    expect(offenders).toEqual([]);
  });

  it("wires the skip link and main-content target in layout", () => {
    const layout = readFileSync(path.join(ROOT, "app", "layout.tsx"), "utf-8");
    expect(layout).toContain("SkipLink");
    expect(layout).toContain('id="main-content"');
    expect(layout).toContain("tabIndex={-1}");
  });

  it("respects prefers-reduced-motion via MotionConfig in providers", () => {
    const providers = readFileSync(path.join(ROOT, "app", "providers.tsx"), "utf-8");
    expect(providers).toContain("MotionConfig");
    expect(providers).toContain('reducedMotion="user"');
  });

  it("has focus-visible and reduced-motion rules in globals.css", () => {
    const css = readFileSync(path.join(ROOT, "app", "globals.css"), "utf-8");
    expect(css).toContain(":focus-visible");
    expect(css).toContain("prefers-reduced-motion");
    expect(css).toContain(".skip-link");
  });

  it("keeps the skip-link key in all 14 locales", () => {
    const locales = ["fa", "en", "ar", "de", "es", "fr", "hi", "it", "ms", "pt", "ru", "ur", "zh", "bn"];
    for (const lg of locales) {
      const json = JSON.parse(
        readFileSync(path.join(ROOT, "locales", `${lg}.json`), "utf-8"),
      ) as { messages: Record<string, string> };
      expect(json.messages["a11y_skip_to_content"], lg).toBeTruthy();
    }
  });

  it("gives range sliders on module pages an accessible name", () => {
    for (const f of ["app/modules/carbon/page.tsx", "app/modules/satellite/page.tsx", "app/modules/scenarios/page.tsx"]) {
      const t = readFileSync(path.join(ROOT, f), "utf-8");
      for (const m of t.matchAll(/<input\b[^>]*type="range"[^>]*>/g)) {
        expect(m[0], `${f}`).toMatch(/aria-label/);
      }
    }
  });
});
