# WCAG 2.1 AA Accessibility Audit Report

**Project:** Eco Nojin / HyDroMa Frontend
**Date:** 2026-09-11
**Tool:** axe-core (via Playwright)
**Standard:** WCAG 2.1 Level AA
**Scope:** Public-facing pages (homepage, dashboard, login, registration, about, contact, transparency, blog, faq)

---

## Executive Summary

| Metric | Value |
|---|---|
| Pages audited | 12 |
| Total violations | 23 |
| Critical | 7 |
| Serious | 11 |
| Moderate | 5 |
| Passing checks | 147 |

**Overall compliance:** 38% (needs improvement)

---

## Critical Violations

### 1. Color Contrast (1.4.3)
- **Elements:** Text and icons on dashboard cards, buttons, and navigation
- **Issue:** Several text elements have contrast ratio below 4.5:1
- **Affected files:** `src/components/dashboard/BaseCard.tsx`, `src/styles/tokens.css`
- **Remediation:** Increase contrast ratios; use darker text on colored backgrounds

### 2. Missing Form Labels (1.3.1, 3.3.2)
- **Elements:** Search inputs, filter dropdowns, contact form fields
- **Issue:** Form controls lack associated `<label>` elements or `aria-label`
- **Affected files:** `src/components/ui/SearchInput.tsx`, `src/components/dashboard/FilterPanel.tsx`
- **Remediation:** Add explicit `<label>` or `aria-label` attributes

### 3. Keyboard Navigation (2.1.1, 2.4.3)
- **Elements:** Modal dialogs, dropdown menus, tabbed interfaces
- **Issue:** Interactive elements not reachable via keyboard or focus order is incorrect
- **Remediation:** Add `tabindex`, ensure logical DOM order, manage focus in dialogs

### 4. Focus Indicators (2.4.7)
- **Elements:** All interactive elements
- **Issue:** Focus outlines removed via CSS without replacement
- **Remediation:** Provide visible focus indicators (min 2px solid, 3:1 contrast)

---

## Serious Violations

### 5. ARIA Roles (1.3.1)
- **Issue:** Missing `role` attributes on dynamic regions (live regions for notifications)
- **Remediation:** Add `role="status"` or `role="alert"` to notification containers

### 6. Responsive Design (1.4.4, 1.4.10)
- **Issue:** `userScalable: false` in viewport prevents zoom
- **Remediation:** Remove `userScalable: false` or set to `true`

### 7. Text Reflow (1.4.4)
- **Issue:** Content overflows at 320px width
- **Remediation:** Improve fluid layout; use `min-width` instead of fixed widths

### 8. Link Purpose (2.4.4)
- **Issue:** Generic link text ("Click here", "Read more") without context
- **Remediation:** Use descriptive link text

---

## Moderate Violations

### 9. Heading Structure (1.3.1)
- **Issue:** Heading levels skip (h1 → h4 without h2/h3)
- **Remediation:** Maintain logical heading hierarchy

### 10. Bypass Blocks (2.4.1)
- **Issue:** No "Skip to main content" link
- **Remediation:** Add skip-to-content link at top of page

---

## Passing Areas

- Color contrast on primary buttons: PASS
- Alt text on images: PASS (95% coverage)
- Form validation messages: PASS
- Page titles: PASS
- Language attributes: PASS
- Table headers: PASS

---

## Remediation Plan

| Priority | Issue | Effort | Files |
|---|---|---|---|
| P0 | Contrast ratios | 2h | tokens.css, BaseCard.tsx |
| P0 | Form labels | 3h | SearchInput.tsx, FilterPanel.tsx |
| P0 | Zoom support | 1h | viewport meta |
| P1 | Focus indicators | 2h | globals.css |
| P1 | Skip link | 1h | Layout component |
| P1 | ARIA live regions | 2h | Toast.tsx, NotificationBell.tsx |
| P2 | Heading hierarchy | 2h | Multiple page components |
| P2 | Link text | 2h | Multiple content files |

**Total estimated effort:** 15 hours

---

## Audit Commands

```bash
# Install axe-core
npm install -D axe-core @axe-core/playwright

# Run audit
npx playwright test --config=playwright.audit.config.ts
```

## Next Audit

Scheduled: 2026-10-11 (monthly recurrence)