"use client";

import { useI18n } from "../lib/i18n-context";

/** Visually-hidden skip link - first focusable element for keyboard users. */
export function SkipLink() {
  const { t } = useI18n();
  return (
    <a href="#main-content" className="skip-link">
      {t("a11y_skip_to_content")}
    </a>
  );
}
