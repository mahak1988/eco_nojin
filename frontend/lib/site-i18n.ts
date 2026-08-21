/**
 * Localized titles for the site chrome (header/footer/nav).
 * - GROUP_TITLES: 11 navigation groups (fa/en)
 * - entryTitle(): registry entry title localized; English from registry.en.json
 *   (falls back to the Persian title when no English map exists).
 */
import enTitles from "../locales/registry.en.json";

export const GROUP_TITLES: Record<string, Record<string, string>> = {
  services: { fa: "خدمات", en: "Services" },
  info: { fa: "سازمان، اخبار و وبلاگ", en: "Organization, News & Blog" },
  support: { fa: "پشتیبانی", en: "Support" },
  community: { fa: "جامعه", en: "Community" },
  science: { fa: "مرکز علم", en: "Science Hub" },
  learn: { fa: "آموزش", en: "Learn" },
  tools: { fa: "ابزار و ماشین‌حساب‌ها", en: "Tools & Calculators" },
  modules: { fa: "ماژول‌ها", en: "Modules" },
  dashboard: { fa: "داشبورد", en: "Dashboard" },
  admin: { fa: "مدیریت", en: "Admin" },
  account: { fa: "حساب کاربری", en: "Account" },
};

export function groupTitle(key: string, locale: string): string {
  const entry = GROUP_TITLES[key];
  if (!entry) return key;
  return entry[locale] ?? entry.fa;
}

export function entryTitle(path: string, titleFa: string, locale: string): string {
  if (locale === "fa") return titleFa;
  const en = (enTitles as Record<string, { title?: string }>)[path];
  return en?.title ?? titleFa;
}
