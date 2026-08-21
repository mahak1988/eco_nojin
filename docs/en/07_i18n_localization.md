# 07. Internationalization and Localization

**Status:** Approved | **Version:** 1.0.0 | **Language:** English

## 1. Scope

The platform targets rural communities across multiple countries; i18n was a
first-class requirement from day one (see `99_conversation_summary.md`).

## 2. Frontend (Next.js / react-i18next)

- **14 locale files** in `frontend/locales/`: en, fa, ar, de, es, fr, hi, it,
  ms, pt, ru, ur, zh, bn.
- Language switcher (`components/LanguageSwitcher.tsx`) with locale state in
  `lib/i18n-context.tsx`.
- RTL support required for fa/ar/ur; the layout currently renders `dir="ltr"`
  — RTL switching is a pending enhancement.
- Backend messages are translated separately via
  `frontend/locales/backend_translations.json` and mapped from backend
  response strings in the panels.

## 3. Backend

- API responses are currently English; translation happens on the frontend
  (key-based mapping of known messages).
- Planned: `Accept-Language` negotiation on the gateway with server-side
  message catalogs.

## 4. USSD/SMS Gateway

- Supports **en, fa, ar** (user-selected per session) — 160-char SMS limit
  and 182-char USSD limit enforced in the engine design.

## 5. Voice (IVR)

- Planned for low-literacy users; languages follow the USSD set initially.

## 6. Content and RAG

- The knowledge base is English-only today; Persian/Arabic retrieval and
  localized agronomic content are planned (FAO-aligned translations).

## 7. Translation Quality Process

- Community/local-agency review for agricultural terminology (no raw machine
  translation for advisory content).
- Glossary per language to be maintained in `docs/` (planned).

## 8. Locale Matrix (current)

| Locale | UI | Backend msgs | RTL | USSD/SMS |
|---|---|---|---|---|
| en | ✅ | ✅ | – | ✅ |
| fa | ✅ | ✅ | pending | ✅ |
| ar | ✅ | ✅ | pending | ✅ |
| others (11) | ✅ | partial | n/a | planned |
