# هماهنگی با Kilo Code — وضعیت، تداخل‌ها و اقدامات

**تاریخ:** ۲۰۲۶/۰۹/۲۹ · **منبع:** `git worktree list`، `.kilo/agent-manager.json`، `git status`

---

## ۱) چه چیزی در حال اجراست

افزونهٔ **Kilo Code** (`kilocode.kilo-code@7.8.1`) در VS Code نصب و در حالت خودگردان تنظیم است:
- `kilo-code.new.agentWorkStyle: "autonomous"` · `autoApprove.enabled: true`
- `kilo-code.new.experimental.multiProject: true` · `browserAutomation.enabled: true` (headless)
- زبان رابط: `fa`

این همان عاملی است که در طول شب گذشته فایل‌های مخزن را موازی با من تغییر می‌داد.

## ۲) سیزده worktree ثبت‌شده

| کارشاخه | آخرین کامیت | تغییرات |
|---|---|---|
| `D:/eco_nojin` (درخت اصلی، `main`) | `5d8e98b8` | **۷۸۳** |
| `feat/marketplace-group-b-v2` ← هدف فعال | `36837253` | ۰ |
| `chore/release-push-audit-v2` | `5f9aa446` | ۰ |
| `feat/public-trust-capabilities-v2` | `5f9aa446` | ۳ |
| `feature/education-pages` | `bcc6042c` | ۱ |
| `feature/legal-pages` | `bcc6042c` | ۱ |
| `feature/qa-validation` | `bcc6042c` | ۱ |
| `feature/science-pages` | `bcc6042c` | ۰ |
| `feature/translations-content` | `bcc6042c` | ۰ |
| `sparkling-advantage` (detached) | `5f9aa446` | ۰ |

**تصحیح یک برداشت اولیه:** پوشهٔ `.kilo/worktrees/feat-phase1-public-pages-completion-…` در `git worktree list` **ثبت نشده** است؛ فرمان‌های git از آن پوشه به مخزن اصلی می‌رسند و همان ۷۸۳ تغییرِ درخت اصلی را گزارش می‌کنند. پس «۷۸۳ تغییرِ آن worktree» در واقع تغییرات همین درخت اصلی است (کار من + کار نشست موازی) — نه یک checkout جدا.

## ۳) ریسک تداخل (اندازه‌گیری‌شده)

- کار Kilo در **worktreeهای جدا** جریان دارد؛ آخرین هدف فعال `feat/marketplace-group-b-v2` است و تمیز (۰ تغییر).
- کار من در **درخت اصلی** است. فایل‌های من (کاتالوگ، پیام‌ها، LanguageMenu، server-env، بازارگاه، اسپک i18n) در درخت اصلی‌اند و در آن worktreeها تغییری ندارند.
- **ریسک واقعی:** ۷۸۳ تغییر در درخت اصلی **هرگز کامیت نشده**. اگر Kilo روی `main` (همین درخت) کار کند یا کاربر `git checkout` بزند، کار تأییدشده (بیلد سبز + تست‌های سبز) از بین می‌رود.

## ۴) اقدامات پیشنهادی (به ترتیب اولویت)

| # | اقدام | چرا |
|---|---|---|
| ۱ | **کامیت کار تأییدشده در `main`** با پیام توصیفی | جلوگیری از از‌دست‌رفتن ۷۸۳ تغییر تأییدشده |
| ۲ | اجرای `.kilo/worktrees` در `.gitignore` | پوشه‌های موقت عامل‌ها نباید در مخزن ردیابی شوند |
| ۳ | پاک‌سازی پوشهٔ کهنهٔ `feat-phase1-public-pages-completion-…` | دیگر worktree ثبت‌شده نیست |
| ۴ | قفل حوزه‌ای: عامل‌های من در `lib/domains/**`، `messages/**`، `lib/config/**` بنویسند و Kilo در worktreeهای خودش | جلوگیری از تداخل فایل |
| ۵ | بررسی پلن‌های Kilo پیش از هر کار موازی | `.kilo/plans/` — ۳ پلن: معماری فرانت‌اند، پروتکل اکوکوین، فلسفهٔ محتوا |

## ۵) پلن‌های موجود Kilo (برای زمینه)

| تاریخ | پلن | حجم |
|---|---|---|
| ۰۹-۲۳ | `site-content-philosophy-plan.md` | ۱۳KB |
| ۰۹-۲۱ | `frontend-architecture-roadmap.md` | ۳۰KB |
| ۰۹-۲۰ | `eco-coin-protocol-plan.md` | ۱۹KB |
